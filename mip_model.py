from gurobipy import Model, GRB, quicksum

class RepairMIP:
    def __init__(self, R, D, P, T, D_p,
                 chi_r_s, tau, tau_p, beta_r, lambda_r,
                 sigma_dpr, chi_dpr_r, pi_r,
                 alpha1, alpha2, alpha3, alpha4, alpha5):
        """
        Initialize the MIP model parameters.
        
        Parameters:
        - R, D, P, T: sets of repairers, defect types, products, time periods
        - D_p: dict mapping product p -> set of defects
        - chi_r_s: shipping cost per batch for repairer r
        - tau: maximum lead time
        - tau_p: dict product -> stock time of p
        - beta_r: max batch capacity per repairer
        - lambda_r: lead time of repairer r
        - sigma_dpr: quality degradation % for defect d on product p by r
        - chi_dpr_r: unit repair cost for defect d on product p by r
        - pi_r: carbon emission per batch shipment to repairer r
        - alpha1..alpha5: weights for objective function
        """
        self.R = R
        self.D = D
        self.P = P
        self.T = T
        self.D_p = D_p
        self.chi_r_s = chi_r_s
        self.tau = tau
        self.tau_p = tau_p
        self.beta_r = beta_r
        self.lambda_r = lambda_r
        self.sigma_dpr = sigma_dpr
        self.chi_dpr_r = chi_dpr_r
        self.pi_r = pi_r
        self.lambda_min = min(lambda_r.values())
        self.alpha1 = alpha1
        self.alpha2 = alpha2
        self.alpha3 = alpha3
        self.alpha4 = alpha4
        self.alpha5 = alpha5
        
        # Create the Gurobi model
        self.model = Model("RepairMIP")
        self.vars = {}  # dictionary to store decision variables

    def optimize(self):
        m = self.model
        R, P, T, D_p = self.R, self.P, self.T, self.D_p
        
        # Decision variables
        x = m.addVars(P, R, T, vtype=GRB.BINARY, name="x")       # product p shipped at t to r
        z = m.addVars(R, T, vtype=GRB.BINARY, name="z")          # batch of r shipped at t
        b = m.addVars(R, T, vtype=GRB.INTEGER, lb=0, name="b")   # accumulated size of batch r at t
        a = m.addVars(R, T, vtype=GRB.INTEGER, lb=0, name="a")   # newly assigned products to r at t
        u = m.addVars(P, R, vtype=GRB.BINARY, name="u")          # assignment product p -> repairer r
        u_dpr = m.addVars([(d,p,r) for p in P for r in R for d in D_p[p]], vtype=GRB.BINARY, name="u_dpr")
        l = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="l")      # total lead time
        eps = m.addVars(P, vtype=GRB.CONTINUOUS, lb=0, name="eps") #penalty for late delivery of product p

        # Store vars for access if needed
        self.vars = {'x': x, 'z': z, 'b': b, 'a': a, 'u': u, 'u_dpr': u_dpr, 'l': l}

        # Constraints
        for r in R:
            for t in T:
                #Constraint 1: Batch size limit
                m.addConstr(b[r,t] <= self.beta_r[r], name=f"b_leq_beta_{r}_{t}")

                
                #Constraint 2: Link batch shipment and size
                m.addConstr(b[r,t] - self.beta_r[r] + 1 <= z[r,t], name=f"b_z_link_{r}_{t}")


                #Constraint 3: Link product shipment and batch shipment
                for p in P:
                    m.addConstr(x[p,r,t] <= z[r,t], name=f"x_z_link_{p}_{r}_{t}")

                
                #Constraint 4: Link batch shipment and product shipment
                m.addConstr(z[r,t] <= quicksum(x[p,r,t] for p in P), name=f"z_x_link_{r}_{t}")

                #Constraint 5: Update accumulated batch size
                if t > 0:
                    m.addConstr(b[r,t] == b[r,t-1] + a[r,t] - quicksum(x[p,r,t] for p in P), name=f"b_update_{r}_{t}")

                #Constraint 6: Update accumulated batch size at t=0
                else:
                    m.addConstr(b[r,t] == a[r,t] - quicksum(x[p,r,t] for p in P), name=f"b_update0_{r}_{t}")

                #Constraint 7: Product shipment cannot exceed available batch size
                m.addConstr(quicksum(x[p,r,t] for p in P) <= (b[r,t-1] if t>0 else 0) + a[r,t], name=f"x_leq_ba_{r}_{t}")

                #Constraint 8: Shipment size cannot exceed the capacity of the batch
                m.addConstr(quicksum(x[p,r,t] for p in P) <= self.beta_r[r], name=f"x_leq_beta_{r}_{t}")
                
        #Constraint 9: Ensure all products are assigned
        m.addConstr(quicksum(a[r,t] for r in R for t in T) == len(self.P), name=f"a_sum")

        #Constraint 10: Each product assigned to exactly one repairer
        for p in P:
            m.addConstr(quicksum(u[p,r] for r in R) == 1, name=f"assignment_{p}")

        #Constraint 11: Link assignments and shipments
        for r in R:
            m.addConstr(quicksum(a[r,t] for t in T) == quicksum(u[p,r] for p in P), name=f"a_u_link_{r}")


        for p in P:
            for r in R:
                #Constraint 12: Link product shipment and assignment
                m.addConstr(quicksum(x[p,r,t] for t in T) <= u[p,r], name=f"x_u_link_{p}_{r}")

                #Constraint 13: Link defect repair and assignment
                m.addConstr(len(D_p[p])*u[p,r] == quicksum(u_dpr[d,p,r] for d in D_p[p]), name=f"u_dpr_link_{p}_{r}")
        
        for p in P:
            #Constraint 14: Lead time calculation
            m.addConstr(self.tau_p[p] + self.lambda_min + quicksum(u[p,r]*(self.lambda_r[r] - self.lambda_min) for r in R) + (1 - quicksum(x[p,r,t] for r in R for t in T))*len(self.T) + quicksum(t*x[p,r,t] for r in R for t in T) <= self.tau, name=f"leadtime_max_{p}")

        for p in P:
            for r in R:     
                #Constraint 15: Lead time lower bound
                m.addConstr(l >= quicksum(x[p,r,t]*(t+self.lambda_r[r] + self.tau_p[p]) for t in T), name=f"leadtime_l_{p}_{r}")
                
               

        
        # Objective function
        obj = (self.alpha1 * l +
               self.alpha2 * quicksum(self.chi_r_s[r]*z[r,t] for r in R for t in T) +
               self.alpha3 * quicksum(self.sigma_dpr[d,p,r]*u_dpr[d,p,r] for p in P for r in R for d in D_p[p]) +
               self.alpha4 * quicksum(self.chi_dpr_r[d,p,r]*u_dpr[d,p,r] for p in P for r in R for d in D_p[p]) +
               self.alpha5 * quicksum(self.pi_r[r]*z[r,t] for r in R for t in T))


        m.setObjective(obj, GRB.MINIMIZE)

        # Optimize
        m.optimize()

        # Store solution
        self.solution = {var.VarName: var.X for var in m.getVars()}
        return self.solution
    
    def get_product_schedule(self):
        """
        Extract scheduling information for each product.
        
        Returns:
            List of dictionaries with scheduling details for each product
        """
        if not hasattr(self, 'solution') or not self.solution:
            raise ValueError("Model has not been optimized yet. Call optimize() first.")
        
        schedule = []
        x = self.vars['x']
        u = self.vars['u']
        u_dpr = self.vars['u_dpr']
        
        for p in self.P:
            # Find assigned repairer
            assigned_repairer = None
            for r in self.R:
                if u[p, r].X > 0.5:  # Binary variable is 1
                    assigned_repairer = r
                    break
            
            if assigned_repairer is None:
                continue
            
            # Find shipping time
            shipping_time = None
            for t in self.T:
                if x[p, assigned_repairer, t].X > 0.5:
                    shipping_time = t
                    break
            
            # Calculate repair cost for this product
            repair_cost = 0
            quality_drop = 0
            for d in self.D_p.get(p, []):
                if u_dpr[d, p, assigned_repairer].X > 0.5:
                    repair_cost += self.chi_dpr_r[d, p, assigned_repairer]
                    quality_drop += self.sigma_dpr[d, p, assigned_repairer]
            
            # Calculate emissions (per batch, but we'll assign proportionally)
            emissions = self.pi_r[assigned_repairer]
            
            # Calculate total lead time
            if shipping_time is not None:
                lead_time = shipping_time + self.lambda_r[assigned_repairer] + self.tau_p[p]
            else:
                lead_time = 0
            
            schedule.append({
                'product_id': p,
                'repairer_id': assigned_repairer,
                'shipping_day': shipping_time if shipping_time is not None else -1,
                'repair_cost': repair_cost,
                'quality_drop': quality_drop,
                'emissions': emissions,
                'lead_time': lead_time,
                'time_in_stock': self.tau_p[p]
            })
        
        return schedule
    
    def get_batch_schedule(self):
        """
        Extract batch shipping schedule.
        
        Returns:
            List of dictionaries with batch shipping information
        """
        if not hasattr(self, 'solution') or not self.solution:
            raise ValueError("Model has not been optimized yet. Call optimize() first.")
        
        batches = []
        z = self.vars['z']
        b = self.vars['b']
        x = self.vars['x']
        
        for r in self.R:
            for t in self.T:
                if z[r, t].X > 0.5:  # Batch shipped
                    # Count products in this batch
                    products_in_batch = []
                    for p in self.P:
                        if x[p, r, t].X > 0.5:
                            products_in_batch.append(p)
                    
                    batches.append({
                        'repairer_id': r,
                        'shipping_day': t,
                        'batch_size': len(products_in_batch),
                        'products': products_in_batch,
                        'shipping_cost': self.chi_r_s[r],
                        'emissions': self.pi_r[r]
                    })
        
        return batches
    
    def get_daily_basket_status(self):
        """
        Get the status of baskets (accumulated products) for each repairer at each day.
        
        Returns:
            Dictionary mapping (repairer_id, day) -> basket_size
        """
        if not hasattr(self, 'solution') or not self.solution:
            raise ValueError("Model has not been optimized yet. Call optimize() first.")
        
        basket_status = {}
        b = self.vars['b']
        a = self.vars['a']
        
        for r in self.R:
            for t in self.T:
                basket_status[(r, t)] = {
                    'accumulated': int(b[r, t].X),
                    'newly_assigned': int(a[r, t].X)
                }
        
        return basket_status




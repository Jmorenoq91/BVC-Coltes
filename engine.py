import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

def calculate_bond_metrics(valuation_date, maturity_date, coupon_rate, ytm, freq, type_tes, base_nominal=100):
    valuation_date = pd.to_datetime(valuation_date).tz_localize(None)
    maturity_date = pd.to_datetime(maturity_date).tz_localize(None)
    
    final_scale = 1000000000 / 100 if type_tes in ['TES COP', 'TCO'] else 1000000 / 100
    cf_list = []
    res = {}

    if freq == 'zero' or str(freq).lower() == 'nan' or freq == 0:
        days_to_mat = (maturity_date - valuation_date).days
        t = days_to_mat / 365
        dirty_price = base_nominal / ((1 + ytm)**t)
        
        cf_list.append({
            '#': 1, 
            'Date': maturity_date.strftime('%Y-%m-%d'),
            'Days': days_to_mat, # Added Days to Maturity
            'Interest': 0, 
            'Principal': base_nominal * final_scale,
            'Total CF': base_nominal * final_scale, 
            'DCF': dirty_price * final_scale
        })
        
        res = {
            "dirty": dirty_price, "accrued": 0, "clean": dirty_price,
            "macaulay": t, "mod_dur": t / (1 + ytm), "convexity": (t**2 + t) / (1 + ytm)**2
        }
    else:
        freq = int(freq)
        dates = []
        curr = maturity_date
        while curr > valuation_date:
            dates.append(curr)
            curr -= relativedelta(months=12//freq)
        dates.sort()
        
        prev_coupon = dates[0] - relativedelta(months=12//freq)
        accrued_int = (coupon_rate / freq) * base_nominal * (max(0, (valuation_date - prev_coupon).days) / (dates[0] - prev_coupon).days)
        
        dirty_price = 0; dur_num = 0; conv_num = 0
        for idx, d in enumerate(dates):
            days_to_cf = (d - valuation_date).days # Calculate days for each flow
            t = days_to_cf / 365
            interest = base_nominal * (coupon_rate / freq)
            principal = base_nominal if d == maturity_date else 0
            pv_cf = (interest + principal) / (1 + ytm)**t
            
            dirty_price += pv_cf
            dur_num += t * pv_cf
            conv_num += (t**2 + t) * pv_cf
            
            cf_list.append({
                '#': idx + 1, 
                'Date': d.strftime('%Y-%m-%d'),
                'Days': days_to_cf, # Added Days to Maturity
                'Interest': interest * final_scale,
                'Principal': principal * final_scale,
                'Total CF': (interest + principal) * final_scale,
                'DCF': pv_cf * final_scale
            })
            
        res = {
            "dirty": dirty_price, "accrued": accrued_int, "clean": dirty_price - accrued_int,
            "macaulay": dur_num / dirty_price,
            "mod_dur": (dur_num / dirty_price) / (1 + ytm),
            "convexity": conv_num / (dirty_price * (1 + ytm)**2)
        }

    res["cf_table"] = pd.DataFrame(cf_list)
    return res
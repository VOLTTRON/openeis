from AppTestingUtils import run_test
import sys

# Test Daily Summary
"""
print("=== Starting Daily Summary Tests ===")

# test same numbers
ds_same_num_ini = "utest_daily_summary/daily_summary_same_number.ini"
ds_same_num_exp = "utest_daily_summary/daily_summary_same_number.ref.csv"
run_test(ds_same_num_ini, [ds_same_num_exp], clean_up=True)
print("========== \n Same numbers test passed. \n========== \n")

# test one to five
ds_onetofive_ini = "utest_daily_summary/daily_summary_onetofive.ini"
ds_onetofive_exp = "utest_daily_summary/daily_summary_onetofive.ref.csv"
run_test(ds_onetofive_ini, [ds_onetofive_exp], clean_up=True)
print("========== \nOne to five test passed.\n========== \n")

# test missing numbers
ds_missing_ini = "utest_daily_summary/daily_summary_missing.ini"
ds_missing_exp = "utest_daily_summary/daily_summary_missing.ref.csv"
run_test(ds_missing_ini, [ds_missing_exp], clean_up=True)
print("========== \nMissing values test passed.\n========== \n")

# test floats
ds_floats_ini = "utest_daily_summary/daily_summary_floats.ini"
ds_floats_exp = "utest_daily_summary/daily_summary_floats.ref.csv"
run_test(ds_floats_ini, [ds_floats_exp], clean_up=True)
print("========== \nFloats test passed.\n========== \n")

#TODO: test floats and missing - still needs to be ironed out
# Weird timing issue.  Probably time zone related.
#ds_floatsmi_ini = "utest_daily_summary/daily_summary_floats_and_missing.ini"
#ds_floatsmi_exp = "utest_daily_summary/daily_summary_floats_and_missing.ref.csv"
#run_test(ds_floatsmi_ini, [ds_floatsmi_exp], clean_up=True)
#print("========== \nFloats and missing test passed.\n========== \n")

#TODO: tests for incorrect input
# Throw exception from application
# Try to catch the exception otherwise complains.
"""

# Energy Signature tests.

print("=== Starting Energy Signature Tests ===")

# Negative one - basic test
es_basic_ini = "utest_energy_signature/energy_signature_negone.ini"
es_basic_exp = ["utest_energy_signature/energy_signature_negone_SP.ref.csv",\
            "utest_energy_signature/energy_signature_negone_WS.ref.csv"]
run_test(es_basic_ini, es_basic_exp, clean_up=True)
print("========== \nBasic test passed.\n========== \n")

es_basic_ini = "utest_energy_signature/energy_signature_missing.ini"
es_basic_exp = ["utest_energy_signature/energy_signature_missing_SP.ref.csv",\
            "utest_energy_signature/energy_signature_missing_WS.ref.csv"]
run_test(es_basic_ini, es_basic_exp, clean_up=True)
print("========== \nMissing test passed. \n========== \n")


#TODO: Same number should break
#es_same_num_ini = "energy_signature_samenum.ini"
#es_same_num_exp = ["energy_signature_missing_SP.ref.csv",\
#            "energy_signature_missing_WS.ref.csv"]
#run_test(es_same_num_ini, es_same_num_exp, clean_up=True)
#print("========== \nSame number test passed. \n========== \n")


#Heat map test

print("=== Starting Heat Map Tests ===")

hm_basic_ini = "utest_heat_map/heat_map_basic.ini"
hm_basic_exp = ["utest_heat_map/heat_map_basic.ref.csv"]
run_test(hm_basic_ini, hm_basic_exp, clean_up=True)
print("========== \nBasic test passed.\n========== \n")

hm_missing_ini = "utest_heat_map/heat_map_missing.ini"
hm_missing_exp = ["utest_heat_map/heat_map_missing.ref.csv"]
run_test(hm_missing_ini, hm_missing_exp, clean_up=True)
print("========== \nMissing test passed.\n========== \n")

hm_floats_ini = "utest_heat_map/heat_map_floats.ini"
hm_floats_exp = ["utest_heat_map/heat_map_floats.ref.csv"]
run_test(hm_floats_ini, hm_floats_exp, clean_up=True)
print("========== \nFloats test passed.\n========== \n")

hm_floats_missing_ini = "utest_heat_map/heat_map_floats_and_missing.ini"
hm_floats_missing_exp = ["utest_heat_map/heat_map_floats_missing.ref.csv"]
run_test(hm_floats_missing_ini, hm_floats_missing_exp, clean_up=True)
print("========== \nFloats and missing test passed.\n========== \n")


# Load duration test

print("=== Starting Load Duration Tests ===")

ld_basic_ini = "utest_load_duration/load_duration_basic.ini"
ld_basic_exp = ["utest_load_duration/load_duration_basic.ref.csv"]
run_test(ld_basic_ini, ld_basic_exp, clean_up=True)
print("========== \nBasic test passed.\n========== \n")

ld_missing_ini = "utest_load_duration/load_duration_missing.ini"
ld_missing_exp = ["utest_load_duration/load_duration_missing.ref.csv"]
run_test(ld_missing_ini, ld_missing_exp, clean_up=True)
print("========== \nMissing test passed.\n========== \n")

ld_floats_ini = "utest_load_duration/load_duration_floats.ini"
ld_floats_exp = ["utest_load_duration/load_duration_floats.ref.csv"]
run_test(ld_floats_ini, ld_floats_exp, clean_up=True)
print("========== \nFloats test passed.\n========== \n")

ld_floats_missing_ini = "utest_load_duration/load_duration_floats_missing.ini"
ld_floats_missing_exp = ["utest_load_duration/load_duration_floats_missing.ref.csv"]
run_test(ld_floats_missing_ini, ld_floats_missing_exp, clean_up=True)
print("========== \nFloats and missing test passed.\n========== \n")


# Load profiling test

print("=== Starting Load Profiling Tests ===")

lp_basic_ini = "utest_load_profiling/load_profiling_basic.ini"
lp_basic_exp = ["utest_load_profiling/load_profiling_basic.ref.csv"]
run_test(lp_basic_ini, lp_basic_exp, clean_up=True)
print("========== \nBasic test passed.\n========== \n")

lp_missing_ini = "utest_load_profiling/load_profiling_missing.ini"
lp_missing_exp = ["utest_load_profiling/load_profiling_missing.ref.csv"]
run_test(lp_missing_ini, lp_missing_exp, clean_up=True)
print("========== \nMissing test passed.\n========== \n")

lp_floats_ini = "utest_load_profiling/load_profiling_floats.ini"
lp_floats_exp = ["utest_load_profiling/load_profiling_floats.ref.csv"]
run_test(lp_floats_ini, lp_floats_exp, clean_up=True)
print("========== \nFloats test passed.\n========== \n")

lp_floats_missing_ini = "utest_load_profiling/load_profiling_floats_missing.ini"
lp_floats_missing_exp = ["utest_load_profiling/load_profiling_floats_missing.ref.csv"]
run_test(lp_floats_missing_ini, lp_floats_missing_exp, clean_up=True)
print("========== \nFloats and missing test passed.\n========== \n")


# Longitudinal benchmarking test

print("=== Starting Longitudinal Benchmarking Tests ===")

lb_basic_ini = "utest_longitudinal_bm/longitudinal_bm_basic.ini"
lb_basic_exp = ["utest_longitudinal_bm/longitudinal_bm_basic.ref.csv"]
run_test(lb_basic_ini, lb_basic_exp, clean_up=True)
print("========== \nBasic test passed.\n========== \n")

lb_missing_ini = "utest_longitudinal_bm/longitudinal_bm_missing.ini"
lb_missing_exp = ["utest_longitudinal_bm/longitudinal_bm_missing.ref.csv"]
run_test(lb_missing_ini, lb_missing_exp, clean_up=True)
print("========== \nMissing test passed.\n========== \n")

lb_floats_ini = "utest_longitudinal_bm/longitudinal_bm_floats.ini"
lb_floats_exp = ["utest_longitudinal_bm/longitudinal_bm_floats.ref.csv"]
run_test(lb_floats_ini, lb_floats_exp, clean_up=True)
print("========== \nFloats test passed.\n========== \n")

lb_floats_missing_ini = "utest_longitudinal_bm/longitudinal_bm_floats_missing.ini"
lb_floats_missing_exp = \
        ["utest_longitudinal_bm/longitudinal_bm_floats_missing.ref.csv"]
run_test(lb_floats_missing_ini, lb_floats_missing_exp, clean_up=True)
print("========== \nFloats and missing test passed.\n========== \n")



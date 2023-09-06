from mlopskit import make

debug_db = make("cache/feature_store-v1", db_name="debug_tests.db")

model_name = "{{model_name}}"
debug_key = f"{model_name}:debug"
# open test
debug_db.set(debug_key, "1")
# close test
debug_key
debug_db.set(debug_key, "0")

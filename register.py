import srp
import pickle
import os

u = input("Username: ")
p = input("Password: ")

# create salt and verification key (bytes)
salt, vkey = srp.create_salted_verification_key(u, p)

# store hex-encoded values so file is portable
entry = (salt.hex(), vkey.hex())

data = {}
if os.path.exists("server_srp_data.pkl"):
    with open("server_srp_data.pkl", "rb") as f:
        try:
            data = pickle.load(f)
        except Exception:
            data = {}

data[u] = entry

with open("server_srp_data.pkl", "wb") as f:
    pickle.dump(data, f)

print(f"Registered user '{u}' and stored salt/vkey in server_srp_data.pkl")
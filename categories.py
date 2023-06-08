import requests
import concurrent.futures
import json

# Replace {token} with your actual token
token = "{token}"  # It is not required by default to obtain category ids

# Arrays to store categories
main_cats = []
children_cats = []
children_of_children_cats = []

# Function to retrieve and print categories
def print_categories():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Retrieve all categories
    response = session.get("https://api.olx.ba/categories", headers=headers)
    data = response.json()

    if "data" in data:
        categories = data["data"]

        # Print main categories and their IDs
        print("Main Categories:")
        for category in categories:
            category_data = {
                "id": category["id"],
                "name": category["name"]
            }
            main_cats.append(category_data)
            print(f"ID: {category['id']}, Name: {category['name']}")

            # Retrieve and print children categories
            print_children_categories(category["id"], headers)
            print()

# Function to retrieve and print children categories
def print_children_categories(category_id, headers):
    # Retrieve children categories
    response = session.get(f"https://api.olx.ba/categories/{category_id}", headers=headers)
    data = response.json()

    if "data" in data and isinstance(data["data"], list):
        children_categories = data["data"]

        # Print children categories and their IDs
        print("Children Categories:")
        for category in children_categories:
            category_data = {
                "id": category["id"],
                "name": category["name"]
            }
            children_cats.append(category_data)
            print(f"ID: {category['id']}, Name: {category['name']}")
            print_children_of_children_categories(category['id'], headers)

def print_children_of_children_categories(category_id, headers):
    response = session.get(f"https://api.olx.ba/categories/{category_id}", headers=headers)
    data = response.json()

    if "data" in data and isinstance(data["data"], dict):
        category_info = data["data"]
        category_data = {
            "id": category_info["id"],
            "name": category_info["name"]
        }
        children_of_children_cats.append(category_data)
        print("Children of children Categories:")
        print(f"ID: {category_info['id']}, Name: {category_info['name']}")
        # You can further process sub_categories if needed
        # sub_categories = category_info['sub_categories']
        # for sub_category in sub_categories:
        #     print(f"ID: {sub_category['id']}, Name: {sub_category['name']}")
        #     print_children_of_children_categories(sub_category['id'], headers)

# Create a requests session object
session = requests.Session()

# Print categories
print_categories()

# Export main_cats to JSON file
with open("main_cats.json", "w") as file:
    json.dump(main_cats, file, indent=4)

# Export children_cats to JSON file
with open("children_cats.json", "w") as file:
    json.dump(children_cats, file, indent=4)

# Export children_of_children_cats to JSON file
with open("children_of_children_cats.json", "w") as file:
    json.dump(children_of_children_cats, file, indent=4)

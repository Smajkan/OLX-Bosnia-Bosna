import requests

# Replace {token} with your actual token
token = "{token}" #It is not required by default to obtain category ids

# Function to retrieve and print categories
def print_categories():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Retrieve all categories
    response = requests.get("https://api.olx.ba/categories", headers=headers)
    data = response.json()

    if "data" in data:
        categories = data["data"]

        # Print main categories and their IDs
        print("Main Categories:")
        for category in categories:
            print(f"ID: {category['id']}, Name: {category['name']}")

            # Retrieve and print children categories
            print_children_categories(category["id"], headers)
            print()

# Function to retrieve and print children categories
def print_children_categories(category_id, headers):
    # Retrieve children categories
    response = requests.get(f"https://api.olx.ba/categories/{category_id}", headers=headers)
    data = response.json()

    if "data" in data and isinstance(data["data"], list):
        children_categories = data["data"]

        # Print children categories and their IDs
        print("Children Categories:")
        for category in children_categories:
            print(f"ID: {category['id']}, Name: {category['name']}")
            print_children_of_children_categories(category['id'], headers)

def print_children_of_children_categories(category_id, headers):
    response = requests.get(f"https://api.olx.ba/categories/{category_id}", headers=headers)
    data = response.json()

    if "data" in data and isinstance(data["data"], dict):
        category_info = data["data"]
        print("Children of children Categories:")
        print(f"ID: {category_info['id']}, Name: {category_info['name']}")
        # You can further process sub_categories if needed
        # sub_categories = category_info['sub_categories']
        # for sub_category in sub_categories:
        #     print(f"ID: {sub_category['id']}, Name: {sub_category['name']}")
        #     print_children_of_children_categories(sub_category['id'], headers)

# Print categories
print_categories()

```markdown
# OLX.ba Categories - API Example

This code example demonstrates how to retrieve categories (their names and IDs) from the OLX.ba API and export them to JSON files. It utilizes the OLX.ba API to fetch the main categories, their children categories, and children of children categories.

## Prerequisites

Before running the code, make sure you have the following:

- Python 3 installed on your machine.
- The `requests` library installed. You can install it by running the following command:

  ```bash
  pip install requests
  ```

## Getting Started

1. Clone this repository to your local machine or download the code as a ZIP file.
2. Replace `{token}` in the code with your actual OLX.ba API token. If you don't have a token, visit the [OLX.ba API documentation](https://api-documentation.olx.ba/) to learn how to obtain one.
3. Open a terminal or command prompt and navigate to the directory where the code is located.

## Running the Code

To run the script and retrieve the categories from the OLX.ba Categories API, follow these steps:

1. Execute the following command to run the script:

   ```bash
   python categories.py
   ```

   This will fetch the categories from the OLX.ba Categories API, print them to the console, and export them to three separate JSON files: `main_cats.json`, `children_cats.json`, and `children_of_children_cats.json`.

2. After running the script, you can find the generated JSON files in the same directory as the script.

## Customization

- If you want to perform additional processing on the categories, you can uncomment the relevant code sections in the `print_children_of_children_categories` function.
- You can modify the code to suit your specific needs, such as adding error handling or integrating it into a larger project.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).



```

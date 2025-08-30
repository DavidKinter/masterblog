"""
Masterblog Flask Application

A simple blog application that allows users to create, read, and delete
blog posts. Data is stored in a JSON file for persistence.
"""

import json
import os

from flask import Flask, render_template, request, redirect, url_for

# Initializes Flask application
app = Flask(__name__)

# Constants
BLOG_DATA_FILE = "blog_data.json"
DEFAULT_BLOG_STRUCTURE = {
    "max_uid": 0,  # "max_uid" for true unique ID
    "posts":   []
    }


# ========== FILE OPERATIONS ==========

def load_blog_data() -> dict:
    """
    Loads blog data from JSON file.
    Returns default structure if file does not exist or is corrupted.
    """
    # Checks if data file exists
    if not os.path.exists(BLOG_DATA_FILE):
        # No file yet, returns default structure
        return DEFAULT_BLOG_STRUCTURE.copy()  # Prevents accidental override

    # Tries to read the file
    try:
        with open(BLOG_DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError:
        # File exists but is corrupted
        print("Warning: Blog data file is corrupted. Starting fresh.")
        return DEFAULT_BLOG_STRUCTURE.copy()
    except IOError as e:
        # Other file reading errors
        print(f"Error reading file: {e}")
        return DEFAULT_BLOG_STRUCTURE.copy()


def save_blog_data(blog_data: dict) -> None:
    """
    Saves blog data to JSON file.
    """
    try:
        with open(BLOG_DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(blog_data, file, indent=4)
    except IOError as e:
        print(f"Error saving blog data: {e}")


# ========== DATA OPERATIONS ==========

def get_next_uid(blog_data: dict) -> int:
    """
    Generates the next unique ID for a blog post.
    Updates andar returns the max_uid from blog data.
    """
    # Updates the max_uid
    blog_data["max_uid"] += 1
    return blog_data["max_uid"]


def find_post_by_uid(blog_posts: list, post_uid: int) -> dict:
    """
    Finds a blog post by its ID.
    Returns the post dictionary if found, None otherwise.
    """
    for post in blog_posts:
        if post.get("uid") == post_uid:
            return post
    return None


def create_blog_post(
        author: str,
        title: str,
        content: str,
        post_uid: int
        ) -> dict:
    """
    Creates a new blog post dictionary with the given data.
    """
    return {
        "uid":     post_uid,
        "author":  author,
        "title":   title,
        "content": content
        }


def delete_post_from_list(blog_posts: list, post_uid: int) -> bool:
    """
    Removes a post from the blog posts list.
    Returns True if deleted, False if not found.
    """
    # Finds the post
    post_to_delete = find_post_by_uid(blog_posts, post_uid)
    if post_to_delete:
        # Removes it from the list
        blog_posts.remove(post_to_delete)
        return True
    return False


# ========== VALIDATION FUNCTIONS ==========

def extract_form_data() -> tuple:
    """
    Extracts and cleans form data from the current request.
    Returns tuple of (author, title, content).
    """
    # Gets data from form, uses empty string if field missing
    author = request.form.get("author", "").strip()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    return author, title, content


def validate_blog_data(author: str, title: str, content: str) -> str:
    """
    Validates blog post data.
    Returns error message if invalid, empty string if valid.
    """
    if not author:
        return "Author name is required"
    if not title:
        return "Post title is required"
    if not content:
        return "Post content is required"

    # All validations passed
    return ""


# ========== INITIALIZATION FUNCTIONS ==========

def initialize_sample_data() -> None:
    """
    Creates sample blog posts if the data file does not exist.
    """
    if not os.path.exists(BLOG_DATA_FILE):
        # Creates sample data structure with zero-based indexing
        sample_data = {
            "max_uid": 1,
            "posts":   [
                {
                    "uid":     0,
                    "author":  "John Doe",
                    "title":   "First Post",
                    "content": "This is my first post."
                    },
                {
                    "uid":     1,
                    "author":  "Jane Doe",
                    "title":   "Second Post",
                    "content": "This is another post."
                    }
                ]
            }
        save_blog_data(sample_data)
        print("Created sample blog posts")


# ========== ROUTE HANDLERS ==========

@app.route("/")
def index():
    """
    Displays all blog posts on the home page.
    This handles GET requests to the root URL.
    """
    # Step 1: Loads blog data from JSON file
    blog_data = load_blog_data()

    # Step 2: Sends posts to the template for display
    # The template will receive a variable called "posts"
    return render_template("index.html", posts=blog_data["posts"])


@app.route("/add", methods=["GET", "POST"])
def add():
    """
    Handles adding new blog posts.
    GET: Shows the form for creating a post.
    POST: Processes the submitted form data.
    """
    if request.method == "POST":
        # User submitted the form

        # Step 1: Extracts data from form
        author, title, content = extract_form_data()

        # Step 2: Validates the data
        error_message = validate_blog_data(author, title, content)
        if error_message:
            # Validation failed, shows form again with error
            return render_template(
                "add.html",
                error=error_message
                )

        # Step 3: Loads existing blog data
        blog_data = load_blog_data()

        # Step 4: Creates new post with unique ID
        post_uid = get_next_uid(blog_data)
        new_post = create_blog_post(author, title, content, post_uid)

        # Step 5: Adds to list and saves
        blog_data["posts"].append(new_post)
        save_blog_data(blog_data)

        # Step 6: Redirects to home page to see the new post
        return redirect(url_for("index"))

    # GET request - shows the empty form
    return render_template("add.html")


@app.route("/delete/<int:post_uid>")
def delete(post_uid: int):
    """
    Deletes a blog post by its ID.
    The <int:post_uid> captures a number from the URL.
    Example: /delete/5 will call delete(5)
    """
    # Step 1: Loads existing blog data
    blog_data = load_blog_data()

    # Step 2: Tries to delete the post
    was_deleted = delete_post_from_list(blog_data["posts"], post_uid)

    # Step 3: Saves the updated data (max_uid remains unchanged)
    if was_deleted:
        save_blog_data(blog_data)
        print(f"Post {post_uid} deleted successfully")
    else:
        print(f"Post {post_uid} not found")

    # Step 4: Always goes back to home page
    return redirect(url_for("index"))


# ========== MAIN EXECUTION ==========

def main():
    """
    Main function to initialize and run the application.
    """
    # Initializes sample data if needed
    initialize_sample_data()

    # Starts the Flask development server
    # host="0.0.0.0" makes it accessible from any network interface
    # port=5000 is the standard Flask development port
    # debug=True shows detailed error messages (turn off in production!)
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()

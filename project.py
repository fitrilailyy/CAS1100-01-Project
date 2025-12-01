import math
import csv
import turtle

# =========================
#  Drawing / UI helpers
# =========================

screen = turtle.Screen()
screen.title("Internet Usage vs Literacy Rate")

writer = turtle.Turtle()
writer.hideturtle()
writer.penup()
writer.speed(0)

box_turtle = turtle.Turtle()
box_turtle.hideturtle()
box_turtle.penup()
box_turtle.speed(0)

def show_message(text):
    """Clear the screen area, draw a speech box, and write multi-line centered text."""
    writer.clear()
    box_turtle.clear()
    # Draw a simple rounded rectangle speech box
    box_turtle.goto(-350, 230)
    box_turtle.pendown()
    box_turtle.pensize(2)
    box_turtle.setheading(0)
    for _ in range(2):
        box_turtle.forward(700)
        box_turtle.right(90)
        box_turtle.forward(430)
        box_turtle.right(90)
    box_turtle.penup()
    # Write text centered inside the box
    writer.goto(0, 200)
    for line in text.split("\n"):
        writer.write(line, align="center", font=("Garamond", 20, "normal"))
        writer.sety(writer.ycor() - 30)

def log_error(message):
    """Append error or warning messages to an error_log.txt file (best-effort)."""
    try:
        with open("error_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(message + "\n")
    except Exception:
        # If logging fails, ignore to avoid crashing the GUI
        pass

def beep_ok():
    """Simple success beep (may depend on system settings)."""
    print("\a", end="")

def beep_error():
    """Simple error beep (may depend on system settings)."""
    print("\a", end="")

# =========================
#  File / data functions
# =========================

def open_files_gui():
    """
    Use turtle.textinput to ask filenames.
    Max 3 invalid tries, then return (None, None).
    """
    attempts = 0
    while attempts < 3:
        internet_name = screen.textinput(
            "Internet CSV",
            "Enter Internet data CSV filename:"
        )
        literacy_name = screen.textinput(
            "Literacy CSV",
            "Enter Literacy data CSV filename:"
        )

        if internet_name is None or literacy_name is None:
            # user pressed Cancel
            attempts += 1
            show_message(f"File input cancelled.\nAttempts left: {3 - attempts}")
            continue

        try:
            internet_file = open(internet_name, "r", encoding="utf-8")
            literacy_file = open(literacy_name, "r", encoding="utf-8")
            show_message("Files opened successfully.")
            beep_ok()
            return internet_file, literacy_file
        except FileNotFoundError:
            attempts += 1
            show_message(f"Error opening file(s).\nAttempts left: {3 - attempts}")

    show_message("Too many invalid attempts.\nProgram will close.")
    return None, None


def read_rate_file(file_obj, label):
    data = {}
    reader = csv.reader(file_obj)
    header = next(reader, None)
    line_number = 2

    for row in reader:
        if not row or len(row) < 2:
            msg = f"[Warning] Skipping malformed {label} line {line_number}"
            print(msg)
            log_error(msg)
            line_number += 1
            continue

        country = row[0].strip().lower()
        rate_str = row[1].strip()

        try:
            rate = float(rate_str)
            data[country] = rate
        except ValueError:
            msg = (f"[Warning] Skipping {label} line {line_number}: "
                   f"cannot convert '{rate_str}' to float.")
            print(msg)
            log_error(msg)
        line_number += 1

    return data


def build_aligned_lists(internet_data, literacy_data):
    x_values, y_values = [], []
    for c in internet_data:
        if c in literacy_data:
            x_values.append(internet_data[c])
            y_values.append(literacy_data[c])
    return x_values, y_values


def calculate_correlation(x_list, y_list):
    n = len(x_list)
    sum_x = sum(x_list)
    sum_y = sum(y_list)
    sum_x2 = sum(x * x for x in x_list)
    sum_y2 = sum(y * y for y in y_list)
    sum_xy = sum(x_list[i] * y_list[i] for i in range(n))

    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x ** 2) *
                            (n * sum_y2 - sum_y ** 2))
    if denominator == 0:
        raise ValueError("Cannot compute correlation.")

    return numerator / denominator

# =========================
#  Lookup + classification
# =========================

def lookup_countries_gui(internet_data, literacy_data, avg_internet, avg_literacy):
    show_message(
        "Country lookup mode.\n"
        "Type a country name in the dialog.\n"
        "Leave empty or Cancel to return to menu.\n"
        "Max 3 invalid country names per session."
    )

    wrong_attempts = 0

    while True:
        name_input = screen.textinput(
            "Country lookup",
            "Enter country name (or leave blank to exit lookup):"
        )
        if not name_input:  # None or ""
            show_message("Exiting country lookup.\nReturning to main menu...")
            break

        key = name_input.strip().lower()
        internet = internet_data.get(key)
        literacy = literacy_data.get(key)

        if internet is None and literacy is None:
            wrong_attempts += 1
            msg = f"Country lookup failed for '{name_input}'."
            log_error(msg)
            beep_error()
            if wrong_attempts >= 3:
                show_message(
                    f"'{name_input}' not found in either file.\n"
                    "You reached the max invalid attempts.\n"
                    "Returning to main menu..."
                )
                break
            else:
                show_message(
                    f"'{name_input}' not found in either file.\n"
                    f"Attempts left: {3 - wrong_attempts}"
                )
            continue

        # If valid
        # Bold country name as header
        lines = [
            f"{name_input.strip().upper()}",
            ""
        ]
        if internet is not None:
            lines.append(f"  Internet usage: {internet:.2f}%")
        else:
            lines.append("  Internet usage: (no data)")
        if literacy is not None:
            lines.append(f"  Literacy rate: {literacy:.2f}%")
        else:
            lines.append("  Literacy rate: (no data)")

        # Classification if both exist
        if internet is not None and literacy is not None:
            lines.append(f"  (Global avg internet: {avg_internet:.2f}%)")
            lines.append(f"  (Global avg literacy: {avg_literacy:.2f}%)")

            if internet >= avg_internet and literacy >= avg_literacy:
                level = "High internet & high literacy (above global avg)."
            elif internet >= avg_internet and literacy < avg_literacy:
                level = "High internet, lower literacy than global avg."
            elif internet < avg_internet and literacy >= avg_literacy:
                level = "Lower internet, higher literacy than global avg."
            else:
                level = "Lower internet & lower literacy (below global avg)."

            lines.append("  Classification: " + level)

        beep_ok()
        show_message("\n".join(lines))


def show_top_stats(internet_data, literacy_data):
    """
    Show top statistics for either Internet usage or Literacy rate.

    For Internet usage:
        - Show Top 10 countries by value.

    For Literacy rate:
        - Show ALL countries that have the maximum literacy value
          (e.g., all with 1.00), so it's fair even if many share the top rate.
    """
    metric = screen.textinput(
        "Top statistics",
        "Which metric would you like to see?\n"
        "1 - Internet usage\n"
        "2 - Literacy rate\n\n"
        "Enter 1 or 2:"
    )

    if metric is None:
        # user cancelled
        return

    metric = metric.strip()
    if metric == "1":
        # Top 10 internet usage
        if not internet_data:
            show_message("No Internet usage data available.")
            return

        sorted_internet = sorted(
            internet_data.items(),
            key=lambda kv: kv[1],
            reverse=True
        )
        top_int = sorted_internet[:10]

        lines = ["Top 10 Internet Usage (%):"]
        rank = 1
        for country, value in top_int:
            lines.append(f"{rank}. {country.title()} - {value:.2f}%")
            rank += 1

        beep_ok()
        show_message("\n".join(lines))

    elif metric == "2":
        # All countries with maximum literacy
        if not literacy_data:
            show_message("No literacy data available.")
            return

        max_lit = max(literacy_data.values())
        top_countries = [c for c, v in literacy_data.items() if v == max_lit]
        top_countries.sort()

        page_size = 9  # countries per page
        total = len(top_countries)
        if total == 0:
            show_message("No countries found with valid literacy data.")
            return

        num_pages = (total + page_size - 1) // page_size
        current_page = 0

        while current_page < num_pages:
            start = current_page * page_size
            end = min(start + page_size, total)
            chunk = top_countries[start:end]

            lines = [
                "Countries with the highest literacy rate:",
                f"Max literacy value: {max_lit:.2f} "
                "(1.00 = 100% if interpreted as a fraction)",
                "",
                f"Page {current_page + 1} / {num_pages}",
                ""
            ]
            for country in chunk:
                lines.append(f"- {country.title()}")

            beep_ok()
            show_message("\n".join(lines))

            current_page += 1
            if current_page < num_pages:
                # Ask user if they want to see next page
                cont = screen.textinput(
                    "Next page",
                    f"Press OK to see next page ({current_page + 1}/{num_pages}),\n"
                    "or Cancel to return to the main menu."
                )
                if cont is None:
                    break

    else:
        beep_error()
        show_message("Invalid choice for Top statistics.\nPlease enter 1 or 2.")

        
# =========================
#  Main turtle program
# =========================

def main_turtle():
    show_message(
        "Internet Usage vs Literacy Correlation\n"
        "CAS1100-01 Project\n\n"
        "This program uses turtle dialogs instead of the terminal."
    )

    internet_file, literacy_file = open_files_gui()
    if internet_file is None or literacy_file is None:
        # Give user a moment to see the message
        screen.textinput("Exit", "Press OK to close.")
        return

    # Read data
    internet_data = read_rate_file(internet_file, "internet")
    literacy_data = read_rate_file(literacy_file, "literacy")
    internet_file.close()
    literacy_file.close()

    x_values, y_values = build_aligned_lists(internet_data, literacy_data)
    if len(x_values) == 0:
        show_message("No overlapping countries.\nProgram will close.")
        screen.textinput("Exit", "Press OK to close.")
        return

    avg_internet = sum(x_values) / len(x_values)
    avg_literacy = sum(y_values) / len(y_values)

    # Main menu loop
    while True:
        # Draw the main menu on the canvas so previous results are cleared
        show_message(
            "Main Menu\n\n"
            "1 - Look up specific countries\n"
            "2 - Compute correlation\n"
            "3 - Show Top statistics\n"
            "4 - Exit program\n\n"
            "Enter 1, 2, 3, or 4 in the dialog box."
        )

        # Then show a small popup ONLY for the numeric choice
        choice = screen.textinput("Main Menu", "Enter 1, 2, 3, or 4:")

        if choice is None:
            # Treat Cancel as exit
            break

        choice = choice.strip()
        if choice == "1":
            beep_ok()
            lookup_countries_gui(internet_data, literacy_data,
                                 avg_internet, avg_literacy)

        elif choice == "2":
            if len(x_values) < 2:
                show_message("Not enough overlapping countries to compute correlation.")
            else:
                r = calculate_correlation(x_values, y_values)
                beep_ok()
                # Simple interpretation
                if r >= 0.7:
                    interp = "Strong positive correlation."
                elif r >= 0.4:
                    interp = "Moderate positive correlation."
                elif r >= 0.2:
                    interp = "Weak positive correlation."
                elif r > -0.2:
                    interp = "Little or no linear correlation."
                elif r > -0.4:
                    interp = "Weak negative correlation."
                elif r > -0.7:
                    interp = "Moderate negative correlation."
                else:
                    interp = "Strong negative correlation."

                show_message(
                    f"Number of countries used: {len(x_values)}\n"
                    f"Correlation coefficient r = {r:.4f}\n\n"
                    f"Interpretation: {interp}\n\n"
                    "Pearson correlation formula used:\n"
                    "r = [ n Σ(xy) - Σx Σy ] / \n"
                    "    sqrt( [n Σx² - (Σx)²] [n Σy² - (Σy)²] )"
                )
                log_error(f"Correlation computed: r = {r:.4f} using {len(x_values)} countries.")

        elif choice == "3":
            beep_ok()
            show_top_stats(internet_data, literacy_data)

        elif choice == "4":
            confirm = screen.textinput("Exit", "Are you sure you want to exit? (Y/N):")
            if confirm and confirm.strip().lower().startswith("y"):
                beep_ok()
                log_error("Program exit confirmed by user.")
                show_message("Thank you for using this program!")
                break
            else:
                show_message("Exit cancelled. Returning to main menu.")

        else:
            beep_error()
            log_error(f"Invalid menu choice entered: {choice!r}")
            show_message("Invalid menu choice.\nPlease enter 1, 2, 3, or 4.")

    # Wait before closing the window
    screen.textinput("Goodbye", "Press OK to close the window.")
    turtle.bye()


if __name__ == "__main__":
    main_turtle()
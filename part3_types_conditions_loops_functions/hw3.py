#!/usr/bin/env python

from typing import Any

RUN = True
UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"
DATE_SPLITER = "-"
CATEGORY_SPLITER = "::"
DATE_FORMAT_LEN = (2, 2, 4)
INCOME_COMMAND = "income"
COST_CATEGORIES_COMMAND = "cost categories"
COST_COMMAND = "cost"
STATS_COMMAND = "stats"
FEB = 2
MONTH_IN_YEAR = 12
COST_CMD_LEN = 4
STATS_CMD_LEN = CATEGORY_CMD_LEN = 2
INCOME_CMD_LEN = 3
AMOUNT = "amount"
CATEGORY = "category"
DATE = "date"


EXPENSE_CATEGORIES = dict({
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
})


financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    first = year % 400 == 0
    second = (year % 4 == 0 and year % 100 != 0)
    return first or second


def check_date_format(data: tuple[str, ...]) -> bool:
    if len(data) != len(DATE_FORMAT_LEN):
        return False

    d, m, y = data
    return (
        len(d) == DATE_FORMAT_LEN[0]
        and len(m) == DATE_FORMAT_LEN[1]
        and len(y) == DATE_FORMAT_LEN[2]
    )


def get_month_days(month: int, year: int) -> int:
    result = 30 + (month // 8 + month) % 2
    if month == FEB:
        result = 28 + is_leap_year(year)
    return result


def is_date_format(maybe_dt: str) -> bool:
    data = data = tuple(maybe_dt.split(DATE_SPLITER))
    first = not all(i.isdigit() for i in data)
    second = not check_date_format(data)
    return first and second


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    if not is_date_format():
        return None

    day, month, year = map(int, maybe_dt.split(DATE_SPLITER))
    if not all(i > 0 for i in (day, month, year)):
        return None
    if month > MONTH_IN_YEAR:
        return None
    if day > get_month_days(month, year):
        return None

    return day, month, year


def income_handler(amount: float, income_date: str) -> str:
    date = extract_date(income_date)

    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    financial_transactions_storage.append({AMOUNT: amount, DATE: date})
    return OP_SUCCESS_MSG


def check_category(category: str) -> bool:
    for i in EXPENSE_CATEGORIES:
        for j in EXPENSE_CATEGORIES[i]:
            if category == f"{i}{CATEGORY_SPLITER}{j}":
                return True
    return False


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    date = extract_date(income_date)

    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    if not check_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    financial_transactions_storage.append({
        CATEGORY: category_name,
        AMOUNT: amount,
        DATE: date,
    })
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(
        f"{cat}{CATEGORY_SPLITER}{sub}"
        for cat in EXPENSE_CATEGORIES
        for sub in EXPENSE_CATEGORIES[cat]
    )


def stats_handler(report_date: str) -> str:
    date = extract_date(report_date)
    if date is None:
        return INCORRECT_DATE_MSG

    lines = [f"Your statistics as of {date}:\n"]

    total_cap = 0
    income = 0
    expense = []
    for cur in financial_transactions_storage:
        if cur and date <= cur[DATE]:
            if CATEGORY in cur:
                expense.append({
                    CATEGORY: cur.get(CATEGORY),
                    AMOUNT: cur.get(AMOUNT),
                })
                total_cap -= cur.get(AMOUNT)
            else:
                income += cur.get(AMOUNT)
                total_cap += cur.get(AMOUNT)

    lines.append(f"Total: {total_cap:.2f}")
    lines.append(f"Income: {income:.2f}")
    lines.append(f"Expense: {sum(i[AMOUNT] for i in expense):.2f}")
    lines.append("\nDetails (category: amount)\n")

    expense.sort(key=lambda x: x[CATEGORY])
    for i, item in enumerate(expense):
        lines.append(
            "{}. {}: {}".format(i + 1, item[CATEGORY], item[AMOUNT])
        )

    return "\n".join(lines)


def is_income_command(command: str) -> bool:
    cmd = command.split()
    return len(cmd) == INCOME_CMD_LEN and cmd[0] == INCOME_COMMAND


def is_cost_command(command: str) -> bool:
    cmd = command.split()

    is_list = command == COST_CATEGORIES_COMMAND
    is_full = cmd[0] == COST_COMMAND and len(cmd) == COST_CMD_LEN

    return is_list or is_full


def is_stats_command(command: str) -> bool:
    cmd = command.split()
    return cmd[0] == STATS_COMMAND and len(cmd) == STATS_CMD_LEN


def is_category_command(command: str) -> bool:
    cmd = command.split()
    return cmd[0] == STATS_COMMAND and len(cmd) == CATEGORY_CMD_LEN


def command_handler(command: str) -> None:
    cmd = command.split()

    if is_income_command(command):
        print(income_handler(float(cmd[1]), cmd[2]))
        return

    if is_category_command(command):
        print(cost_categories_handler())
        return

    if is_cost_command(command):
        res = cost_handler(
            cmd[1],
            float(cmd[2]),
            cmd[3],
        )
        print(
            res
            if res == OP_SUCCESS_MSG
            else "\n".join([res, cost_categories_handler()]),
        )
        return

    if is_stats_command(command):
        print(stats_handler(cmd[1]))
        return

    print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    while RUN:
        command = input()
        command_handler(command)


if __name__ == "__main__":
    main()

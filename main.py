from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__),"expenses.db")

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__),"categories.json")


mcp = FastMCP("ExpenseTracker")
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT NULL,
                note TEXT DEFAULT NULL
            )
        """)
        conn.commit()

init_db()


@mcp.tool
def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """List all expenses from the database"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("INSERT INTO expenses (date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)", 
                               (date, amount, category, subcategory, note))
        return {"status": "success", "message": "Expense added successfully", "id": cur.lastrowid}

@mcp.tool
def get_expenses():
    """List all expenses from the database"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT id ,date, amount, category, subcategory, note FROM expenses ORDER BY date DESC")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

@mcp.tool
def get_expenses_by_date(start_date: str, end_date: str):
    """List all expenses from the database by date"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT id ,date, amount, category, subcategory, note FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC", (start_date, end_date))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

@mcp.tool
def update_expense(id: int, date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Update an expense in the database"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE expenses SET date = ?, amount = ?, category = ?, subcategory = ?, note = ? WHERE id = ?", (date, amount, category, subcategory, note, id))

@mcp.tool
def delete_expense(id: int):
    """Delete an expense from the database"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
        return {"status": "success", "message": "Expense deleted successfully"}

@mcp.tool
def get_expense_schema():
    """Get the schema of the expenses table"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("PRAGMA table_info(expenses)")
        cols = [d[1] for d in cur.fetchall()]
        return cols
@mcp.tool
def get_category_summary_by_date(start_date: str, end_date: str):
    """Returns total spending grouped by category, sorted highest to lowest."""
    expenses = get_expenses_by_date(start_date, end_date)
    if not expenses:
        return {
            "highest_spending_category": None,
            "summary": []
        }
    category_totals: dict[str, float] = {}
    for expense in expenses:
        cat = expense["category"]
        category_totals[cat] = category_totals.get(cat, 0) + expense["amount"]
    sorted_summary = sorted(
        [{"category": cat, "total": round(total, 2)} for cat, total in category_totals.items()],
        key=lambda x: x["total"],
        reverse=True
    )
    return {
        "highest_spending_category": sorted_summary[0]["category"],
        "total_categories": len(sorted_summary),
        "summary": sorted_summary
    }

@mcp.tool()
def get_category_summary() -> dict:
    """Returns total spending grouped by category, sorted highest to lowest."""

    expenses = get_expenses()  

    if not expenses:
        return {
            "highest_spending_category": None,
            "summary": []
        }

    category_totals: dict[str, float] = {}
    for expense in expenses:
        cat = expense["category"]
        category_totals[cat] = category_totals.get(cat, 0) + expense["amount"]

    sorted_summary = sorted(
        [{"category": cat, "total": round(total, 2)} for cat, total in category_totals.items()],
        key=lambda x: x["total"],
        reverse=True
    )

    return {
        "highest_spending_category": sorted_summary[0]["category"],
        "total_categories": len(sorted_summary),
        "summary": sorted_summary
    }


@mcp.tool
def commit_changes():
    """Commit changes to the database"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.commit()
        return {"status": "success", "message": "Changes committed successfully"}

@mcp.tool
def rollback_changes():
    """Rollback changes to the database"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.rollback()
        return {"status": "success", "message": "Changes rolled back successfully"}

#Adding categories so that any ai agent dont add categories that are not in the categories.json file
#prevents random categories being added to the database and inconsistant categories being added to the database


@mcp.resource("expenses://categories", mime_type="application/json")
def get_categories():
    """Get all categories from the database"""
    with open(CATEGORIES_PATH, "r") as f:
        return f.read()  





if __name__ == "__main__":
    mcp.run(transport="http" , host="0.0.0.0", port=8000)


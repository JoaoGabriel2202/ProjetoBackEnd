from fastapi import FastAPI, HTTPException
from collections import Counter
import json
import os

app = FastAPI()

livros = []
usuarios = []
emprestimos = []


def save_data():
    with open("books.json", "w") as f:
        json.dump(livros, f)
    with open("users.json", "w") as f:
        json.dump(usuarios, f)
    with open("loans.json", "w") as f:
        json.dump(emprestimos, f)

def load_data():
    global livros, usuarios, emprestimos
    try:
        with open("books.json", "r") as f:
            livros = json.load(f)
        with open("users.json", "r") as f:
            usuarios = json.load(f)
        with open("loans.json", "r") as f:
            emprestimos = json.load(f)
    except FileNotFoundError:
        livros, usuarios, emprestimos = [], [], []

load_data()

@app.on_event("shutdown")
def shutdown_event():
    save_data()

@app.get("/")
def root():
    return {"message": "Bem-vindo à API da Biblioteca!"}

@app.post("/books/")
def create_book(book: dict):
    book['id'] = len(livros) + 1
    book['available_copies'] = book.get("available_copies", 1)
    livros.append(book)
    return book

@app.get("/books/")
def get_books():
    return livros

@app.put("/books/{book_id}")
def update_book(book_id: int, book_data: dict):
    book = next((b for b in livros if b["id"] == book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    book.update(book_data)
    return book

@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    global livros
    livros = [b for b in livros if b["id"] != book_id]
    return {"message": "Livro removido com sucesso"}

@app.post("/users/")
def create_user(user: dict):
    user['id'] = len(usuarios) + 1
    usuarios.append(user)
    return user

@app.get("/users/")
def get_users():
    return usuarios

@app.post("/loans/")
def create_loan(loan: dict):
    book = next((b for b in livros if b["id"] == loan["book_id"]), None)
    if not book or book["available_copies"] <= 0:
        raise HTTPException(status_code=400, detail="Livro indisponível")

    user_loans = [l for l in emprestimos if l["user_id"] == loan["user_id"] and not l["returned"]]
    if len(user_loans) >= 3:
        raise HTTPException(status_code=400, detail="Usuário já atingiu o limite de empréstimos")

    loan['id'] = len(emprestimos) + 1
    loan['returned'] = False
    emprestimos.append(loan)
    book["available_copies"] -= 1
    return loan

@app.put("/loans/{loan_id}/return")
def return_loan(loan_id: int):
    loan = next((l for l in emprestimos if l["id"] == loan_id), None)
    if not loan or loan["returned"]:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado ou já devolvido")

    loan["returned"] = True
    book = next((b for b in livros if b["id"] == loan["book_id"]), None)
    if book:
        book["available_copies"] += 1
    return {"message": "Livro devolvido com sucesso"}

@app.get("/reports/most-loaned-books")
def most_loaned_books():
    book_count = Counter([loan["book_id"] for loan in emprestimos if not loan["returned"]])
    most_loaned = [{"book_id": book_id, "times_loaned": count} for book_id, count in book_count.most_common()]
    return most_loaned

@app.get("/reports/users-with-pending-loans")
def pending_loans():
    pending = [
        {
            "user_id": loan["user_id"],
            "book_id": loan["book_id"],
            "loan_id": loan["id"]
        }
        for loan in emprestimos if not loan["returned"]
    ]
    return pending


app_port = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=app_port)

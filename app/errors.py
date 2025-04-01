from flask import render_template

from app import app, db


@app.errorhandler(404)  # page not found error
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)  # internal server error
def internal_errror(error):
    db.session.rollback()
    return render_template("500.html"), 500

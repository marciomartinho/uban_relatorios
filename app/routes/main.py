"""
Blueprint para rotas principais
"""
from flask import Blueprint, render_template

# Criar blueprint
main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    """Página inicial"""
    return render_template('home.html', title='Home')

@main.route('/sobre')
def sobre():
    """Página sobre o sistema"""
    return render_template('sobre.html', title='Sobre')
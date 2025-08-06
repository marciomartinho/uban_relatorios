"""
Blueprint principal para Balanço Geral GDF
Página que lista todos os quadros demonstrativos disponíveis
Arquivo: app/routes/balanco_geral/balanco_geral.py
"""
from flask import Blueprint, render_template

# Criar blueprint sem url_prefix (será definido no registro)
balanco_geral = Blueprint('balanco_geral', __name__)

@balanco_geral.route('/')
def index():
    """Página principal do Balanço Geral GDF com todos os quadros"""
    return render_template('balanco_geral/balanco_geral.html',
                         title='Balanço Geral GDF - Quadros Demonstrativos')
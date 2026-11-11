import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def carregar_script():
    spec = importlib.util.spec_from_file_location("gerar_relatorio", RAIZ / "scripts" / "gerar_relatorio.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_relatorio_tem_todas_as_secoes_e_o_aviso_de_dados_sinteticos():
    html = carregar_script().montar(RAIZ / "resultados", sintetico=True)
    for trecho in ("Resumo executivo", "Método", "Resultados", "Interpretação", "Limitações",
                   "riscos psicossociais (PGR)", "Dados sintéticos", "Autorrelato",
                   "Recorte transversal", "Amostra pequena", "Rastreamento, não diagnóstico"):
        assert trecho in html
    assert "130 respondentes" in html


def test_relatorio_do_repositorio_esta_atualizado():
    html = carregar_script().montar(RAIZ / "resultados", sintetico=True)
    assert (RAIZ / "resultados" / "relatorio.html").read_text(encoding="utf-8") == html


def test_relatorio_nao_tem_pizza_nem_horario():
    html = (RAIZ / "resultados" / "relatorio.html").read_text(encoding="utf-8").lower()
    assert "pizza" not in html and "hora de" not in html

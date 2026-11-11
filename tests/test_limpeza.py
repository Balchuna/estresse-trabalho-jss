import pandas as pd
import pytest

from jss import limpeza
from jss.limpeza import (
    COLUNAS_PERGUNTAS,
    ESCALA_CONCORDANCIA,
    ESCALA_FREQUENCIA,
    agrupar_setores_pequenos,
    decodificar,
    eh_coluna_pessoal,
    limpar,
    limpar_unidade,
    normalizar_texto,
    validar_mesmas_perguntas,
)

NBSP = " "
PERGUNTAS = [f"Pergunta {i}" for i in range(1, 18)]


def escrever(tmp_path, nome, linhas, *, perguntas=PERGUNTAS, pessoais=True, email=False,
             codificacao="utf-8", separador=","):
    """Monta um CSV pequeno. `linhas` é uma lista de (setor, [17 respostas])."""
    cab = (["ID", "Hora de início", "Hora de conclusão"] if pessoais else [])
    cab += (["Email"] if email else []) + ["Em qual setor você trabalha"] + list(perguntas)
    texto = [separador.join(cab)]
    for i, (setor, respostas) in enumerate(linhas, start=1):
        campos = ([str(i), "1/1/26 8:00:00", "1/1/26 8:05:00"] if pessoais else [])
        campos += (["fulano@exemplo.com"] if email else []) + [setor] + list(respostas)
        texto.append(separador.join(campos))
    caminho = tmp_path / nome
    caminho.write_bytes("\r\n".join(texto).encode(codificacao))
    return caminho


def respostas(freq="Às vezes", conc="Discordo"):
    return [freq] * 11 + [conc] * 6


def test_normalizar_texto_tira_nbsp_e_espacos():
    assert normalizar_texto(f"{NBSP}Às  vezes {NBSP}") == "Às vezes"


@pytest.mark.parametrize("nome", ["ID", "Hora de início", "Hora de conclusão ", "Email", "E-mail", f"{NBSP}Nome"])
def test_colunas_pessoais_sao_reconhecidas(nome):
    assert eh_coluna_pessoal(nome)


def test_setor_e_perguntas_nao_sao_pessoais():
    assert not eh_coluna_pessoal("Em qual setor você trabalha")
    assert not eh_coluna_pessoal("Pergunta 1")


def test_decodifica_utf8_com_bom_e_cp1252():
    assert decodificar("Às vezes".encode("utf-8-sig")) == ("Às vezes", "utf-8")
    assert decodificar("Às vezes".encode("cp1252")) == ("Às vezes", "cp1252")


def test_colunas_pessoais_nao_chegam_na_tabela(tmp_path):
    caminho = escrever(tmp_path, "u.csv", [("A", respostas())] * 5, email=True)
    tabela, info = limpeza.ler_sem_dados_pessoais(caminho)
    assert info["colunas_pessoais_removidas"] == 4
    assert len(tabela.columns) == 18
    assert "fulano@exemplo.com" not in tabela.to_csv()
    assert "8:00:00" not in tabela.to_csv()


def test_saida_tem_so_unidade_setor_e_q01_a_q17(tmp_path):
    caminho = escrever(tmp_path, "u.csv", [("A", respostas())] * 5, email=True)
    unidade = limpar_unidade(caminho, "Unidade 1")
    assert list(unidade.dados.columns) == ["unidade", "setor"] + COLUNAS_PERGUNTAS
    assert set(unidade.dados["unidade"]) == {"Unidade 1"}


def test_cp1252_e_ponto_e_virgula(tmp_path):
    caminho = escrever(tmp_path, "u.csv", [("Produção", respostas())] * 5,
                       codificacao="cp1252", separador=";")
    unidade = limpar_unidade(caminho, "Unidade 1")
    assert unidade.qualidade["codificacao"] == "cp1252"
    assert unidade.dados.loc[0, "setor"] == "Produção"
    assert unidade.dados.loc[0, "q01"] == "Às vezes"


def test_espacos_e_nbsp_somem_de_respostas_setores_e_cabecalhos(tmp_path):
    perguntas = [NBSP + PERGUNTAS[0]] + PERGUNTAS[1:-1] + [PERGUNTAS[-1] + NBSP]
    linha = ("PCP/Qualidade ", [f"Frequentemente{NBSP}", "Às vezes "] + ["Raramente"] * 9
             + [f"Concordo totalmente{NBSP}"] * 6)
    caminho = escrever(tmp_path, "u.csv", [linha] * 5, perguntas=perguntas)
    unidade = limpar_unidade(caminho, "Unidade 1")
    assert unidade.perguntas == PERGUNTAS
    assert unidade.dados.loc[0, "setor"] == "PCP/Qualidade"
    assert unidade.dados.loc[0, "q01"] == "Frequentemente"
    assert unidade.dados.loc[0, "q02"] == "Às vezes"
    assert unidade.dados.loc[0, "q12"] == "Concordo totalmente"


def test_resposta_vazia_ou_fora_da_escala_vira_ausente_e_e_contada(tmp_path):
    errada = respostas()
    errada[0] = ""
    errada[1] = "Talvez"
    errada[11] = "Frequentemente"  # escala certa só para as 11 primeiras
    caminho = escrever(tmp_path, "u.csv", [("A", errada)] + [("A", respostas())] * 4)
    unidade = limpar_unidade(caminho, "Unidade 1")
    assert unidade.dados.loc[0, ["q01", "q02", "q12"]].isna().all()
    assert unidade.qualidade["respostas_vazias"] == 1
    assert unidade.qualidade["respostas_fora_da_escala"] == 2
    assert unidade.dados.loc[1:, COLUNAS_PERGUNTAS].notna().all().all()


def test_escalas_por_posicao(tmp_path):
    caminho = escrever(tmp_path, "u.csv", [("A", respostas())] * 5)
    dados = limpar_unidade(caminho, "Unidade 1").dados
    assert set(dados[COLUNAS_PERGUNTAS[:11]].stack()) <= set(ESCALA_FREQUENCIA)
    assert set(dados[COLUNAS_PERGUNTAS[11:]].stack()) <= set(ESCALA_CONCORDANCIA)


def test_setor_vazio_vira_nao_informado(tmp_path):
    caminho = escrever(tmp_path, "u.csv", [("", respostas())] * 5)
    assert set(limpar_unidade(caminho, "Unidade 1").dados["setor"]) == {"Não informado"}


def test_numero_errado_de_perguntas_falha(tmp_path):
    caminho = escrever(tmp_path, "u.csv", [("A", respostas()[:16])], perguntas=PERGUNTAS[:16])
    with pytest.raises(ValueError, match="esperava 17 perguntas, achei 16"):
        limpar_unidade(caminho, "Unidade 1")


def test_sem_coluna_de_setor_falha(tmp_path):
    caminho = tmp_path / "u.csv"
    caminho.write_text(",".join(PERGUNTAS) + "\n" + ",".join(respostas()), encoding="utf-8")
    with pytest.raises(ValueError, match="coluna de setor"):
        limpar_unidade(caminho, "Unidade 1")


def test_mesmas_perguntas_ignora_espacos_e_caixa():
    outras = [NBSP + PERGUNTAS[0].upper()] + PERGUNTAS[1:]
    validar_mesmas_perguntas(PERGUNTAS, outras)


def test_perguntas_diferentes_falham_sem_citar_o_texto():
    outras = PERGUNTAS[:3] + ["Texto secreto"] + PERGUNTAS[4:]
    with pytest.raises(ValueError) as erro:
        validar_mesmas_perguntas(PERGUNTAS, outras)
    assert "[4]" in str(erro.value)
    assert "secreto" not in str(erro.value)


def tabela_setores(contagens):
    linhas = [(u, s) for (u, s), n in contagens.items() for _ in range(n)]
    return pd.DataFrame(linhas, columns=["unidade", "setor"])


def test_setor_com_menos_de_5_vira_outros_por_unidade():
    dados = tabela_setores({("U1", "A"): 5, ("U1", "B"): 4, ("U1", "C"): 1, ("U2", "B"): 6})
    saida, resumo = agrupar_setores_pequenos(dados)
    assert saida.groupby(["unidade", "setor"]).size().to_dict() == {
        ("U1", "A"): 5, ("U1", "Outros"): 5, ("U2", "B"): 6}
    assert resumo["setores_agrupados_em_outros"] == 2
    assert resumo["respondentes_em_outros"] == 5
    assert resumo["unidades_com_outros_abaixo_do_minimo"] == []


def test_outros_abaixo_do_minimo_e_avisado():
    dados = tabela_setores({("U1", "A"): 5, ("U1", "B"): 3})
    _, resumo = agrupar_setores_pequenos(dados)
    assert resumo["unidades_com_outros_abaixo_do_minimo"] == ["U1"]


def test_limpar_junta_valida_e_embaralha_de_forma_reprodutivel(tmp_path):
    u1 = escrever(tmp_path, "u1.csv", [("A", respostas("Raramente"))] * 6 + [("B", respostas())] * 2)
    u2 = escrever(tmp_path, "u2.csv", [("A", respostas())] * 5, email=True)
    dados, qualidade = limpar(u1, u2)
    de_novo, _ = limpar(u1, u2)
    pd.testing.assert_frame_equal(dados, de_novo)
    assert qualidade["total_de_respondentes"] == 13
    assert qualidade["unidades_com_outros_abaixo_do_minimo"] == ["Unidade 1"]
    assert list(dados["unidade"]) != sorted(dados["unidade"])  # ordem original perdida


def test_limpar_falha_se_as_unidades_tem_perguntas_diferentes(tmp_path):
    u1 = escrever(tmp_path, "u1.csv", [("A", respostas())] * 5)
    u2 = escrever(tmp_path, "u2.csv", [("A", respostas())] * 5,
                  perguntas=PERGUNTAS[:16] + ["Outra pergunta"])
    with pytest.raises(ValueError, match=r"\[17\]"):
        limpar(u1, u2)

import base64

def salvar_rancho_apps_script(ordem, numero, nome_arquivo, arquivo_bytes):
    b64 = base64.b64encode(arquivo_bytes).decode("utf-8")

    payload = {
        "acao": "salvar",
        "ordem": str(ordem).strip(),
        "numero": str(numero).strip(),
        "nome": nome_arquivo,
        "b64": b64
    }

    r = requests.post(APPS_SCRIPT_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    if not data.get("ok"):
        raise Exception(data.get("erro", "Falha ao salvar rancho"))

    return data

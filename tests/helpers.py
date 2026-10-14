"""Ferramentas compartilhadas pelos testes."""


def make_pdf(paginas):
    """Cria um PDF mínimo. `paginas` é uma lista de textos; "" = página em branco."""
    partes = [b"%PDF-1.4\n"]
    offsets = []

    def add(corpo):
        offsets.append(sum(len(p) for p in partes))
        partes.append(corpo)

    n = len(paginas)
    primeira = 4
    kids = " ".join(f"{primeira + 2 * i} 0 R" for i in range(n))
    add(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    add(f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {n} >>\nendobj\n".encode())
    add(b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n")

    for i, texto in enumerate(paginas):
        pid, cid = primeira + 2 * i, primeira + 2 * i + 1
        add(
            f"{pid} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {cid} 0 R "
            f"/Resources << /Font << /F1 3 0 R >> >> >>\nendobj\n".encode()
        )
        if texto:
            seguro = texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream = b"BT /F1 12 Tf 50 740 Td (" + seguro.encode("cp1252") + b") Tj ET"
        else:
            stream = b""
        add(f"{cid} 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream\nendobj\n")

    inicio_xref = sum(len(p) for p in partes)
    total = len(offsets) + 1
    xref = f"xref\n0 {total}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    trailer = f"trailer\n<< /Size {total} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n"
    return b"".join(partes) + xref.encode() + trailer.encode()

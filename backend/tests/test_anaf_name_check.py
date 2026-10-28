from app.agents.verificator import anaf


def test_same_company_ignores_legal_form_and_diacritics():
    assert anaf.same_company("Agro Prahova Distribuție SRL", "AGRO PRAHOVA DISTRIBUTIE S.R.L.") is True
    assert anaf.same_company("Agro Prahova Distribuție SRL", "MOLDOVAN IOAN - FINEL ÎNTREPRINDERE INDIVIDUALĂ") is False
    assert anaf.same_company(None, "X SRL") is None


def test_real_company_with_other_name_is_not_attributed():
    """Review PR #11: CUI-ul inventat 40211937 există la ANAF ca o altă firmă (activă)."""
    other = anaf.Company(name="MOLDOVAN IOAN - FINEL ÎNTREPRINDERE INDIVIDUALĂ", cui="40211937", active=False,
                         founded=None, source="anaf")
    out = anaf.check_company(other, "anaf", "doc_2", "[CUI_1]", declared_name="Agro Prahova Distribuție SRL")
    assert [f.code for f in out] == ["COMPANY_NAME_MISMATCH"]  # nu COMPANY_INACTIVE al firmei străine
    same = anaf.Company(name="AGRO PRAHOVA DISTRIBUTIE SRL", cui="40211937", active=False, founded=None, source="anaf")
    assert [f.code for f in anaf.check_company(same, "anaf", "doc_2", "[CUI_1]",
                                               declared_name="Agro Prahova Distribuție SRL")] == ["COMPANY_INACTIVE"]

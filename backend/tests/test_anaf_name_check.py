from app.agents.verificator import anaf


def test_same_company_ignores_legal_form_and_diacritics():
    assert anaf.same_company("Agro Prahova Distribuție SRL", "AGRO PRAHOVA DISTRIBUTIE S.R.L.") is True
    assert anaf.same_company("Agro Prahova Distribuție SRL", "EXEMPLU ALTĂ FIRMĂ ÎNTREPRINDERE INDIVIDUALĂ") is False
    assert anaf.same_company(None, "X SRL") is None


def test_real_company_with_other_name_is_not_attributed():
    """Review PR #11: un CUI de pe document care la ANAF aparține altei firme nu primește starea acelei firme."""
    other = anaf.Company(name="EXEMPLU ALTĂ FIRMĂ ÎNTREPRINDERE INDIVIDUALĂ", cui="9402119372", active=False,
                         founded=None, source="anaf")
    out = anaf.check_company(other, "anaf", "doc_2", "[CUI_1]", declared_name="Agro Prahova Distribuție SRL")
    assert [f.code for f in out] == ["COMPANY_NAME_MISMATCH"]  # nu COMPANY_INACTIVE al firmei străine
    same = anaf.Company(name="AGRO PRAHOVA DISTRIBUTIE SRL", cui="9402119372", active=False, founded=None,
                        source="anaf")
    assert [f.code for f in anaf.check_company(same, "anaf", "doc_2", "[CUI_1]",
                                               declared_name="Agro Prahova Distribuție SRL")] == ["COMPANY_INACTIVE"]

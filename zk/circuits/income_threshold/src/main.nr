// Afirmatia: "venitul meu net lunar, atestat de angajator pentru aceasta cerere, e >= prag".
// Banca vede doar pragul, angajamentul (commitment) si nonce-ul cererii - nu salariul.
// Semnatura angajatorului pe commitment se verifica in afara circuitului (in backend).
fn main(salary_bani: u64, salt: Field, threshold_bani: pub u64, commitment: pub Field, case_nonce: pub Field) {
    let h = std::hash::pedersen_hash([salary_bani as Field, salt, case_nonce]);
    assert(h == commitment, "angajament invalid");
    assert(salary_bani >= threshold_bani, "venit sub prag");
}

#[test]
fn accepta_venit_peste_prag() {
    let c = std::hash::pedersen_hash([850000, 42, 7]);
    main(850000, 42, 500000, c, 7);
}

#[test(should_fail_with = "venit sub prag")]
fn respinge_venit_sub_prag() {
    let c = std::hash::pedersen_hash([300000, 42, 7]);
    main(300000, 42, 500000, c, 7);
}

#[test(should_fail_with = "angajament invalid")]
fn respinge_nonce_altei_cereri() {
    let c = std::hash::pedersen_hash([850000, 42, 7]);
    main(850000, 42, 500000, c, 8);
}

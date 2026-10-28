// Ajutor pentru angajator: calculeaza angajamentul cu ACELASI hash ca circuitul principal
// (evita reimplementarea Pedersen pe Grumpkin in Python). Rulat cu `nargo execute`.
fn main(salary_bani: u64, salt: Field, case_nonce: Field) -> pub Field {
    std::hash::pedersen_hash([salary_bani as Field, salt, case_nonce])
}

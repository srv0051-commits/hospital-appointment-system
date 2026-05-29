const doctor = document.getElementById("doctor");
const patients = document.getElementById("patients");
const price = document.getElementById("price");

function calculatePrice() {
    const fees = {
        "General": 300,
        "Cardiologist": 800,
        "Dermatologist": 500
    };

    let selectedDoctor = doctor.value;
    let patientCount = patients.value;

    if (patientCount > 0) {
        let total = fees[selectedDoctor] * patientCount;
        price.innerText = "Estimated Fee: ₹" + total;
    }
}

doctor.addEventListener("change", calculatePrice);
patients.addEventListener("input", calculatePrice);
// ==========================
// GLOBAL STATE
// ==========================

let packetId = null;


// ==========================
// CREATE PACKET
// ==========================
async function createPacket() {
    const res = await fetch("/api/create", {
        method: "POST"
    });

    const data = await res.json();

    window.location = "/packet/" + data.id;
}


// ==========================
// LOAD PACKET DATA
// ==========================
async function loadPacket(pid) {

    packetId = pid;

    const res = await fetch("/api/packet/" + pid);
    const data = await res.json();

    if (data.error) {
        document.body.innerHTML = "Packet not found";
        return;
    }

    renderPacket(data);
}


// ==========================
// RENDER PACKET UI
// ==========================
function renderPacket(data) {

    // Update progress
    const progress = Math.floor(
        (data.claimsCount / data.maxParticipants) * 100
    );

    document.getElementById("progressBar").style.width = progress + "%";
    document.getElementById("remaining").innerText =
        data.remainingAmount.toFixed(2);

    // Sort ranking
    const sorted = data.claims.sort((a, b) => b.amount - a.amount);

    let html = "";

    sorted.forEach((c, index) => {
        html += `
        <div class="claim-row">
            <div>${index + 1}</div>
            <div>${c.wallet.slice(0,6)}...${c.wallet.slice(-4)}</div>
            <div>$${c.amount}</div>
        </div>
        `;
    });

    document.getElementById("claimList").innerHTML = html;
}


// ==========================
// CLAIM
// ==========================
async function claim() {

    const address = document.getElementById("address").value;

    const res = await fetch("/api/claim/" + packetId, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ address })
    });

    const data = await res.json();

    const result = document.getElementById("result");

    if (data.success) {
        result.innerText = "🎉 You got $" + data.amount;
        loadPacket(packetId);
    } else {
        result.innerText = data.error;
    }
}

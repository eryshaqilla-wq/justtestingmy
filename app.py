from flask import Flask, request, jsonify, redirect, render_template_string
import uuid
import random
import re
from datetime import datetime

app = Flask(__name__)

packets = {}
MAX_PARTICIPANTS = 20
TOTAL_AMOUNT = 100.0

def is_valid_address(addr):
    return re.match(r"^0x[a-fA-F0-9]{40}$", addr)

# ===============================
# HOME PAGE
# ===============================
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gacha Red Packet</title>
<style>
body{
    margin:0;
    font-family:Arial;
    background:#f5f5f5;
    text-align:center;
    padding:40px 20px;
}
.logo{font-size:80px;margin-bottom:10px;}
.title{font-size:38px;font-weight:bold;color:#facc15;}
.subtitle{color:#9ca3af;margin-top:10px;}
.desc{margin-top:20px;font-size:18px;color:#444;line-height:1.5;}
.button{
    margin-top:40px;
    background:#facc15;
    border:none;
    padding:18px;
    width:100%;
    max-width:350px;
    border-radius:35px;
    font-size:20px;
    font-weight:bold;
    cursor:pointer;
}
.footer{margin-top:60px;color:#9ca3af;font-size:14px;}
</style>
</head>
<body>

<div class="logo">🧧</div>
<div class="title">Gacha Red Packet</div>
<div class="subtitle">Agent-Powered USDC Airdrops on Base</div>
<div class="desc">
Create a USDC pool and share a link — recipients claim random amounts like a lottery!
</div>

<form action="/create" method="post">
<button class="button">🧧 Create Red Packet</button>
</form>

<div class="footer">
Powered by Virtuals ACP · Base · USDC
</div>

</body>
</html>
"""

# ===============================
# CREATE PACKET
# ===============================
@app.route("/create", methods=["POST"])
def create():
    pid = str(uuid.uuid4())

    packets[pid] = {
        "remaining": TOTAL_AMOUNT,
        "claims": [],
        "count": 0
    }

    return redirect(f"/claim/{pid}")

# ===============================
# CLAIM PAGE
# ===============================
@app.route("/claim/<pid>")
def claim_page(pid):

    if pid not in packets:
        return "Invalid packet", 404

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Red Packet</title>
<style>
body{
    margin:0;
    font-family:Arial;
    background:#c62828;
    padding:30px 20px;
    color:white;
}
.header{
    text-align:center;
    margin-bottom:30px;
}
.card{
    background:white;
    color:black;
    padding:25px;
    border-radius:20px;
    max-width:380px;
    margin:auto;
}
.btn{
    background:#facc15;
    border:none;
    padding:15px;
    width:100%;
    border-radius:30px;
    font-size:18px;
    font-weight:bold;
    cursor:pointer;
    margin-top:15px;
}
input{
    width:100%;
    padding:12px;
    border-radius:10px;
    border:1px solid #ddd;
    margin-top:15px;
}
.success{color:green;margin-top:10px;}
.error{color:red;margin-top:10px;}
.claim-row{
    background:#ef5350;
    color:white;
    padding:12px;
    margin-top:10px;
    border-radius:15px;
    display:flex;
    justify-content:space-between;
}
#formBox{display:none;}
</style>

<script>
function openClaim(){
    document.getElementById("startBtn").style.display="none";
    document.getElementById("formBox").style.display="block";
}

async function claim(){

    const address=document.getElementById("address").value;

    const res=await fetch("/api/claim/{{pid}}",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({address:address})
    });

    const data=await res.json();
    const result=document.getElementById("result");

    if(data.success){
        result.className="success";
        result.innerText="🎉 You got $"+data.amount;
        loadList();
    }else{
        result.className="error";
        result.innerText=data.error;
    }
}

async function loadList(){

    const res=await fetch("/api/packet/{{pid}}");
    const data=await res.json();

    let html="";
    data.claims.sort((a,b)=>b.amount-a.amount);

    data.claims.forEach((c,i)=>{
        html+=`
        <div class="claim-row">
            <div>${i+1}</div>
            <div>${c.wallet.slice(0,6)}...${c.wallet.slice(-4)}</div>
            <div>$${c.amount}</div>
        </div>`;
    });

    document.getElementById("list").innerHTML=html;
}

window.onload=loadList;
</script>

</head>
<body>

<div class="header">
<h1>🧧 Red Packet</h1>
</div>

<div class="card">

<button id="startBtn" class="btn" onclick="openClaim()">
Klik di sini untuk claim
</button>

<div id="formBox">
<input type="text" id="address" placeholder="Paste EVM address 0x...">
<button class="btn" onclick="claim()">Claim</button>
</div>

<div id="result"></div>

<h3 style="margin-top:25px;">Recent Claims</h3>
<div id="list"></div>

</div>

</body>
</html>
""", pid=pid)

# ===============================
# API GET PACKET
# ===============================
@app.route("/api/packet/<pid>")
def api_packet(pid):
    if pid not in packets:
        return jsonify({"error":"not found"}),404
    return jsonify(packets[pid])

# ===============================
# API CLAIM
# ===============================
@app.route("/api/claim/<pid>", methods=["POST"])
def api_claim(pid):

    if pid not in packets:
        return jsonify({"error":"not found"}),404

    packet=packets[pid]

    data=request.get_json()

    if not data or "address" not in data:
        return jsonify({"error":"Address required"})

    address=data["address"]

    if not is_valid_address(address):
        return jsonify({"error":"Invalid address format"})

    if address.lower() in [c["wallet"] for c in packet["claims"]]:
        return jsonify({"error":"Already claimed"})

    if packet["count"]>=MAX_PARTICIPANTS:
        return jsonify({"error":"Packet depleted"})

    remaining_slots=MAX_PARTICIPANTS-packet["count"]

    if remaining_slots==1:
        amount=round(packet["remaining"],2)
    else:
        max_amount=packet["remaining"]/remaining_slots*2
        amount=round(random.uniform(0.5,max_amount),2)

    packet["remaining"]-=amount
    packet["count"]+=1

    packet["claims"].append({
        "wallet":address.lower(),
        "amount":amount,
        "time":datetime.utcnow().isoformat()+"Z"
    })

    return jsonify({"success":True,"amount":amount})

if __name__=="__main__":
    app.run(host="127.0.0.1",port=5000)
    
    import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
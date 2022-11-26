
window.onload=function() {
    var update = setInterval(function() { getPlayers(); }, 5000);
    getPlayers();
};

function getPlayers() {
  // the url to add items to the cart is stored in a hidden field in our html
  var urlList = document.getElementById("url-cmd-list").value;
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
  if (this.readyState != 4) {
      return;
    }
    updatePlayers(this.responseText);
  };
  xhttp.open("GET", urlList, true);
  xhttp.send();
}

function updatePlayers(jsonReturn) {

  jsonReturn = JSON.parse(jsonReturn);
  var count = jsonReturn["max"];
  var max = jsonReturn["count"];
  var players = jsonReturn["players"];

  var divPlayers = document.getElementById("players");
  divPlayers.innerHTML = 
		"<b>There are " + max + " of " + count + " players:</b></br>";
  divPlayers.innerHTML += players.join(" &middot ");

}


window.onload=function() {
    var update = setInterval(function() { getPlayers(); }, 5000);
    getPlayers();
};

function getPlayers() {
  var urlList = document.getElementById("url-cmd-list").value;
  fetch(urlList, {
    method: "GET",
  })
  .then(response => response.json())
  .then(response => updatePlayers(response));
}

function updatePlayers(jsonReturn) {

  var count = jsonReturn["max"];
  var max = jsonReturn["count"];
  var players = jsonReturn["players"];

  var divPlayers = document.getElementById("players");
  divPlayers.innerHTML = 
		"<b>There are " + max + " of " + count + " players:</b></br>";
  divPlayers.innerHTML += players.join(" &middot ");

}

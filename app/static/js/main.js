
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

  var urlPlayer = document.getElementById("url-main-player").value;
  for (let i = 0; i < players.length; i++) {
    player = players[i];
    players[i] = "<a href=" + urlPlayer + player + ">" + player + "</a>";
  }

  var divPlayers = document.getElementById("players");
  divPlayers.innerHTML = 
		"<b>There are " + max + " of " + count + " players:</b></br>";
  divPlayers.innerHTML += players.join(" &middot ");

}

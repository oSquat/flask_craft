// We're using https://www.cssscript.com/flash-toast-message/
// to flash messages back to the user

window.onload=function() {
    var btnKick = document.getElementById("btnKick");
    btnKick.onclick = function() { kick() };
};

function kickResponse(response) {
  // flash a message indicating server response
  // expects response json containing:
  //	status: success or failure, matches "color" of notify()
  //    response: a message from the server
  var color = null;
  if (response['result'] == 'success') {
    color = "success"
  } else {
    color = "danger"
  };
  notify({
    message: response['response'],
    color: color,
    timeout: 5000
  });
};

function kick() {
  
  var urlKick = document.getElementById("url-cmd-kick").value;
  var player = document.getElementById("value-player").value;

  fetch(urlKick, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({"player": player})
  })
  .then(response => response.json())
  .then(response => kickResponse(response));
};

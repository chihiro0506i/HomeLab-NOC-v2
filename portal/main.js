(function () {
  const hostname = window.location.hostname || "raspberrypi.local";
  const hostLabel = document.getElementById("hostLabel");
  const pihole = document.getElementById("piholeLink");
  const netalertx = document.getElementById("netalertxLink");
  const uptime = document.getElementById("uptimeLink");

  if (hostLabel) hostLabel.textContent = `Host: ${hostname}`;
  if (pihole) pihole.href = `http://${hostname}:8081/admin`;
  if (netalertx) netalertx.href = `http://${hostname}:20211`;
  if (uptime) uptime.href = `http://${hostname}:3001`;
})();

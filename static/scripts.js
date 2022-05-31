// Slider counter
var slider = document.getElementById("rangeslider");
var number = document.getElementById("rangeval");
number.innerHTML = slider.value;
slider.oninput = function() {
    number.innerHTML = this.value;
}
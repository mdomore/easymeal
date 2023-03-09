// Array to store Meals
var meals = [
  "Viande - légumes plancha",
	"Tomates farcies",
	"Tomates - mozza",
	"Tartiflette",
	"Steak haché - frites",
	"Soupe - croûtons",
	"Salade lardons",
	"Salade epinard - poulet - parmesan - tomates confites",
	"Salade caesar",
	"Riz chinois",
	"Risotto speck - petits pois",
	"Risotto chorizo - petits pois",
	"Raviolis frais - sauce tomate",
	"Ratatouille",
	"Raclette",
	"Quiche lorraine - quiche saumon",
	"Quiche carottes - courgettes",
	"Pâtes à la viande",
	"Pâtes à la carbonara",
	"Pâtes sauce",
	"Pâtes roquette",
	"Pâtes noisettes - salade - parmesan",
	"Pâtes au saumon",
	"Pâtes Udon - poulet",
	"Purée - saucisses",
	"Poulet papillotte - riz",
	"Potimarron - carottes - marrons - four",
	"Pommes de terre - Carottes - Courgettes - Saucisse",
	"Pomme de terre - carottes rôties",
	"Poissons - riz",
	"Pizza",
	"Omelette - salade",
	"Oeufs à la coque",
	"Melon - jambon",
	"Lentilles - saucisses",
	"Lasagnes maison",
	"Jardinière de légumes",
	"Hâchis parmentier maison",
	"Haricots verts - lardons - pdt",
	"Grâtin pommes de terre - carottes",
	"Grâtin macaronis - jambon",
	"Gougères - salade",
	"Galettes",
	"Escalope à la crème - riz",
	"Croque-mozza",
	"Croque-monsieur",
	"Couscous",
	"Cordons bleus - petits pois",
	"Chili con carne",
	"Buritos",
	"Boulettes viande - semoule",
  "Tempura de légumes",
  "Poulet Teriyaki - riz, concombres",
  "Poisson - Haricots verts",
  "Poulet aux pruneaux - riz sarfané - oignons",
];

// Array to store tags
var tags = [
  "été",
	"à commander",
	"week-end",
	"sans enfants",
	"rapide",
	"pâtes",
	"long",
	"hiver",
	"facile",
	"double repas",
	"disabled",
	"dîner",
	"déjeuner",
];

// Array to store week days
var days = [
  "mon",
  "tues",
  "wed",
  "thurs",
  "fri",
  "sat",
  "sun",
]

//

// Loop to generate a random meal for each meal in the week
for (day of days) {
  var randomNumber = Math.floor(Math.random() * meals.length);
  $("." + day +" .meal.lunch .meal-title").text(meals[randomNumber]);
  var randomNumber = Math.floor(Math.random() * meals.length);
  $("." + day +" .meal.diner .meal-title").text(meals[randomNumber]);
}

// Refresh button implementation
$(".option-refresh").click(function(e) {
  // console.log($(this).closest(".meal").children(".meal-title"));
  e.preventDefault();
  var randomNumber = Math.floor(Math.random() * meals.length);
  $(this).closest(".meal").children(".meal-title").text(meals[randomNumber]);
  return false;
})


// Disable button implementation
$(".option-xmark").click(function(e) {
  // console.log($(this).closest(".meal").children(".meal-title").css("display"));
  e.preventDefault();
  if (($(this).closest(".meal").children(".meal-title").css("display") === "none")) {
    $(this).closest(".meal").children(".meal-title").fadeIn();
  } else {
    $(this).closest(".meal").children(".meal-title").fadeOut();
  }
})

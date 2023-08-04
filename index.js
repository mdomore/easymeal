// Array to store Meals
var meals = [
	{
		"name": "Viande - légumes plancha",
		"link": ""
	},
	{
		"name": "Tomates farcies",
		"link": ""
	},
	{
		"name": "Tomates - mozza",
		"link": ""
	},
	{
		"name": "Tartiflette",
		"link": ""
	},
	{
		"name": "Steak haché - frites",
		"link": ""
	},
	{
		"name": "Soupe - croûtons",
		"link": ""
	},
	{
		"name": "Salade lardons",
		"link": ""
	},
	{
		"name": "Salade epinard - poulet - parmesan - tomates confites",
		"link": ""
	},
	{
		"name": "Salade caesar",
		"link": ""
	},
	{
		"name": "Riz chinois",
		"link": ""
	},
	{
		"name": "Risotto speck - petits pois",
		"link": ""
	},
	{
		"name": "Risotto chorizo - petits pois",
		"link": ""
	},
	{
		"name": "Raviolis frais - sauce tomate",
		"link": ""
	},
	{
		"name": "Ratatouille",
		"link": ""
	},
	{
		"name": "Raclette",
		"link": ""
	},
	{
		"name": "Quiche lorraine - quiche saumon",
		"link": ""
	},
	{
		"name": "Quiche carottes - courgettes",
		"link": ""
	},
	{
		"name": "Pâtes à la viande",
		"link": ""
	},
	{
		"name": "Pâtes à la carbonara",
		"link": ""
	},
	{
		"name": "Pâtes sauce",
		"link": ""
	},
	{
		"name": "Pâtes roquette",
		"link": ""
	},
	{
		"name": "Pâtes noisettes - salade - parmesan",
		"link": ""
	},
	{
		"name": "Pâtes au saumon",
		"link": ""
	},
	{
		"name": "Pâtes Udon - poulet",
		"link": ""
	},
	{
		"name": "Purée - saucisses",
		"link": ""
	},
	{
		"name": "Poulet papillotte - riz",
		"link": ""
	},
	{
		"name": "Potimarron - carottes - marrons - four",
		"link": ""
	},
	{
		"name": "Pommes de terre - Carottes - Courgettes - Saucisse",
		"link": ""
	},
	{
		"name": "Pomme de terre - carottes rôties",
		"link": ""
	},
	{
		"name": "Poissons - riz",
		"link": ""
	},
	{
		"name": "Pizza",
		"link": ""
	},
	{
		"name": "Omelette - salade",
		"link": ""
	},
	{
		"name": "Oeufs à la coque",
		"link": ""
	},
	{
		"name": "Melon - jambon",
		"link": ""
	},
	{
		"name": "Lentilles - saucisses",
		"link": ""
	},
	{
		"name": "Lasagnes maison",
		"link": ""
	},
	{
		"name": "Jardinière de légumes",
		"link": ""
	},
	{
		"name": "Hâchis parmentier maison",
		"link": ""
	},
	{
		"name": "Haricots verts - lardons - pdt",
		"link": ""
	},
	{
		"name": "Grâtin pommes de terre - carottes",
		"link": ""
	},
	{
		"name": "Grâtin macaronis - jambon",
		"link": ""
	},
	{
		"name": "Gougères - salade",
		"link": ""
	},
	{
		"name": "Galettes",
		"link": ""
	},
	{
		"name": "Escalope à la crème - riz",
		"link": ""
	},
	{
		"name": "Croque-mozza",
		"link": ""
	},
	{
		"name": "Croque-monsieur",
		"link": ""
	},
	{
		"name": "Couscous",
		"link": ""
	},
	{
		"name": "Cordons bleus - petits pois",
		"link": ""
	},
	{
		"name": "Chili con carne",
		"link": ""
	},
	{
		"name": "Buritos",
		"link": ""
	},
	{
		"name": "Boulettes viande - semoule",
		"link": ""
	},
	{
		"name": "Tempura de légumes",
		"link": ""
	},
	{
		"name": "Poulet Teriyaki - riz, concombres",
		"link": ""
	},
	{
		"name": "Poisson - Haricots verts",
		"link": ""
	},
	{
		"name": "Poulet aux pruneaux - riz sarfané - oignons",
		"link": ""
	},
	{
		"name": "Curry de chou-fleur rôti et lentilles corail",
		"link": "https://radisrose.fr/curry-chou-fleur-roti-lentilles-corail/"
	},
	{
		"name": "Gaufres salées à la Patate douce",
		"link": "https://cuisine-addict.com/gaufres-salees-a-la-patate-douce/"
	},
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
  $("." + day +" .meal.lunch .meal-title").text(meals[randomNumber].name);
	if ( meals[randomNumber].link != ""){
		$("." + day +" .meal.lunch .href-link").attr({"href": meals[randomNumber].link,
																									"target": "_blank",
																									"rel": "noopener noreferrer"});
	}
  var randomNumber = Math.floor(Math.random() * meals.length);
  $("." + day +" .meal.diner .meal-title").text(meals[randomNumber].name);
	if ( meals[randomNumber].link != ""){
		$("." + day +" .meal.diner .href-link").attr({"href": meals[randomNumber].link,
																									"target": "_blank",
																									"rel": "noopener noreferrer"});
	}
}

// Refresh button implementation
$(".option-refresh").click(function(e) {
  // console.log($(this).closest(".meal").children(".meal-title"));
  e.preventDefault();
  var randomNumber = Math.floor(Math.random() * meals.length);
  $(this).closest(".meal").children(".meal-title").text(meals[randomNumber].name);
	if ( meals[randomNumber].link != ""){
		$(this).closest(".meal").children(".href-link").attr({"href": meals[randomNumber].link,
																													"target": "_blank",
																													"rel": "noopener noreferrer"});
	}
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


function setAttributes(element, attributes) {
  Object.keys(attributes).forEach(attr => {
    element.setAttribute(attr, attributes[attr]);
  });
}
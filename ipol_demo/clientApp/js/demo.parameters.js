var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var parameters = parameters ||  {};
var parametersType = parametersType || {};

var params = {};
var ddl_params = {};
var demoInfo = helpers.getFromStorage('demoInfo');

parameters.printParameters = function() {
  params,
  ddl_params = {};
  demoInfo = helpers.getFromStorage('demoInfo');

  if (demoInfo.params) {
    var demoInfoParams = demoInfo.params;
    addParametersSectionButtons();
    $('.param-container').remove();
    for (var i = 0; i < demoInfoParams.length; i++) {
      var param = demoInfoParams[i];
      var functionName = $.fn[param.type];
      ddl_params[param.id] = param;

      if ($.isFunction(functionName)) {
        addToParamsObject(param);
        printParameter(param, i);
      } else console.error(param.type + ' param type is not correct');
    }
    if (demoInfo.params_layout) addLayout();
  }
}

function printParameter(param, index) {
  $('<div class=param-' + index + '></div>').appendTo('#parameters-container').addClass('param-container');
  $('<div class=param-content-' + index + ' ></div>').appendTo('.param-' + index).addClass("param-content");

  $('.param-content-' + index)[param.type](param, index);

  $('.param-' + index).addClass(param.id);
  $('.' + param.id).checkVisibility(param);

  if (param.values) addMaxMin(param, index);
  if (param.comments) addParamInfo(param, index);
}

function addToParamsObject(param) {
  if (param.default_value != undefined ||  param.values != undefined) {
    params[param.id] = param.default_value != undefined ? param.default_value : param.values.default;
  }
}

function addMaxMin(param, index) {
  $('.param-content-' + index).append("<div id=maxmin-" + index + " class=maxmin ></div>");
  if (param.values.max) $('#maxmin-' + index).append("<span> Max: " + param.values.max + "</span>");
  if (param.values.min) $('#maxmin-' + index).append("<span> Min: " + param.values.min + "</span>");
}

function addParamInfo(param, index) {
  $('.param-' + index).append("<div class=param-comments >" + param.comments + "</div>");
}

function addLayout() {
  for (let i = 0; i < demoInfo.params_layout.length; i++) {
    var firstLayoutElement = demoInfo.params_layout[i];
    $(".param-" + firstLayoutElement[1][0]).addLayoutHeader(firstLayoutElement[0]);
  }
}

function updateParamsArrayValue(param_id, value) {
  params[param_id] = value;
  checkParamsVisibility();
}

function checkParamsVisibility() {
  for (let i = 0; i < Object.keys(params).length; i++) {
    $('.' + Object.keys(params)[i]).checkVisibility(ddl_params[Object.keys(params)[i]]);
  }
}

function getConcatDescription() {
  var description = "";
  for (let i = 0; i < demoInfo.general.param_description.length; i++) {
    description += demoInfo.general.param_description[i];
  }
  return description
};

function addParametersSectionButtons() {
  $('.params-buttons').remove();
  $('#parameters-container').append('<div class=params-buttons ></div>');
  addDescriptionButton();
  addResetButton();
}

function addDescriptionButton() {
  $('.params-buttons').append('<button class=param-description-btn >Description</button>');
  $('.param-description-btn').addClass('btn');
  $('.params-description-dialog').addParamsDescription();
  $('.param-description-btn').click(function() {
    $(".params-description-dialog").dialog("open");
  });
}

function addResetButton() {
  $('.params-buttons').append('<button class=param-reset-btn >Reset</button>');
  $('.param-reset-btn').addClass('btn');
  $('.param-reset-btn').click(function(event) {
    parameters.printParameters();
  });;
}

$.fn.addParamsDescription = function() {
  $(this).empty().append(getConcatDescription());
}

$.fn.checkVisibility = function(param) {
  if (param.visible != undefined)
    if (!eval(param.visible)) $('.' + param.id).addClass('di-none');
    else $('.' + param.id).removeClass('di-none');
  else $('.' + param.id).removeClass('di-none');
}

// Print upper the layout items the layout header.
$.fn.addLayoutHeader = function(label) {
  $("<div class=label-param></div>").insertBefore($(this))
    .addClass('param-container')
    .append('<h3>' + label + '</h3>');
}

$(".params-description-dialog").dialog({
  resizable: false,
  autoOpen: false,
  width: 700,
  modal: true,
  open: function() {
    $('.ui-widget-overlay').on('click', function() {
      $('.params-description-dialog').dialog('close');
    })
  }
});

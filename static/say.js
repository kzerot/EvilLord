/**
 * @author Max
 */


String.prototype.format = function () {
  var args = arguments;
  return this.replace(/\{\{|\}\}|\{(\d+)\}/g, function (m, n) {
    if (m == "{{") { return "{"; }
    if (m == "}}") { return "}"; }
    return args[n];
  });
};

function closeThis(f) {
  $(f).parent().remove();
}

function selectHero (id) {
  if(id == null || id == '')
  	id = 'town';
  $("#phraseTo").val(id);
  $('.messageBox').hide();
  if($('#messages'+id).length > 0)
  {
  	$('#messages'+id).show();
  }
  else{
  	$('#allmessages').append("<div id='messages"+ id +"' class='messageBox'><div class='firstmessage'>Ололо - гирой приветствуэ!</div></div>")
  }
}

function getHero (id) {
	request=  $.ajax({
           /*type: "GET",*/
           dataType: "json",
           url: '/getinfo',
           data: {id : id, type : 'hero'}, 
           success: addInfo
         });
}

function addInfo(data)
{
	$('body').append(data['html']);
	    $(".infoForm").draggable(
    	{
    		handle:".infoCaption",
    	}
    );
    $(".infoCaption").disableSelection();
}

function addToChat(bigdata){
	
   	if(bigdata && bigdata['data']){
   		for (d in bigdata['data']){
   		data = bigdata['data'][d]; 		
   		   	console.log(data);
   		if(data['answers'] || data['buildings'] || data['heroes'])
		   	{
		   		var to = data['sayTo'];
		   		console.log($('#messages' + to + ' .firstmessage'))
		   		if (data['answers']){
		   			$("#sayForm").removeAttr('disabled');
					$("#sayInput").val("");
		   			for(var answer in data['answers']){
		
		   				var p = $('#messages' + to + ' .firstmessage').after(data['answers'][answer]).next();
		   				console.log(p.html());
		   				p.hide();
		   				p.delay(answer*600 + 100).slideDown(600);
		   				
		   			}
		   		}
		   		if(data['buildings'] && data['buildings'].length>0){
				
		   			$("#buildings").empty();
		   			for (b in data['buildings']){
		   				building = data['buildings'][b];
			   			$("#buildings").append(building);
					}
		   		}
		   		if(data['heroes'] && data['heroes'].length>0){
		   			$("#heroes").empty();
		   			for (h in data['heroes']){
		   				hero = data['heroes'][h];
			   			$("#heroes").append(hero);
					}
		   		}
		   	}	
		}	
   	}
}

function sendSay(){
	$("#sayForm").attr('disabled', 'disabled');
    $.ajax({
           type: "POST",
           url: '/say',
           data: $("#sayForm").serialize(), 
           success: addToChat
         });
    return false;
}

function update(){
	    $.ajax({
           /*type: "GET",*/
           dataType: "json",
           url: '/say',
           success: addToChat
         });
}

$(document).ready(function() { 
	$("#sayBtn").click(sendSay);
	$( document ).tooltip();
	var updateTimer = setInterval(update, 100);
	 $( "#sortableLeft, #sortableRight" ).sortable({
      connectWith: ".connected",
      handle:".minicaption",
      placeholder: "p-holder"
    }).disableSelection();
    
    $(".infoForm").draggable(
    	{
    		handle:".infoCaption",
    	}
    );
    $(".minicaption").disableSelection();
	
}); 
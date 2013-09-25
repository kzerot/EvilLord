/**
 * @author Max
 */


function validatePass(){
	if($("#password").val()!=$("#reppassword").val()){
		$("#reppassword").addClass("notvalide");
	}
	else{
		$("#reppassword").removeClass("notvalide");
	}
}

$(document).ready(function() { 
	console.log($("#reppassword"));
	$("#reppassword").bind("propertychange keyup input paste", validatePass);
	$("#password").bind("propertychange keyup input paste", validatePass);
}); 
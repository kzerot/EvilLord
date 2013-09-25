var engine = {};

engine.mapData = null;  // no map data yet

engine.setMap = function(mapData)
{
   engine.mapData = mapData;
};

engine.outhnd = document.getElementById('output');
engine.canvas = document.getElementById('canvas');
engine.handle = engine.canvas.getContext('2d');


engine.output = function(message)
{
   engine.outhnd.innerHTML =  message;
};


engine.screen = {};
engine.screen.width  = engine.canvas.width;
engine.screen.height = engine.canvas.height;
engine.screen.tilesX = engine.canvas.width  / 16;
engine.screen.tilesY = engine.canvas.height / 16;

engine.viewport = {};
engine.viewport.x = 0;
engine.viewport.y = 0;

engine.tile = {};
engine.tile.draw = function(x, y, tile)
{
   engine.handle.fillText(tile, x * 16, y * 16);
};

engine.map = {};
engine.map.draw = function()
{
	console.log('draw');
   engine.handle.clearRect(0,0,engine.canvas.width,engine.canvas.height);
   var i, j;

   var mapX = 0;
   var mapY = 0;
   var tile;

   engine.output('drawing map from ' + engine.viewport.x + ',' + engine.viewport.y + ' to ' + (engine.viewport.x + engine.screen.tilesX) + ',' + (engine.viewport.y + engine.screen.tilesY));

   for(j=0; j<engine.screen.tilesY; j++)
   {
      for(i=0; i<engine.screen.tilesX; i++)
      {
         mapX = Math.round(i + engine.viewport.x);
         mapY =  Math.round(j + engine.viewport.y);
         tile = (engine.mapData[mapY] && engine.mapData[mapY][mapX]) ? engine.mapData[mapY][mapX] : ' ';
         engine.tile.draw(i, j, tile);
      }
   }
};

engine.events = {
	isDragging : false,
	initialX : 0,
	initialY : 0,
	
	mouseMove : function(event){
		event.preventDefault();
		if (engine.events.isDragging){
		    var x = event.x;
		    var y = event.y;
		    
			engine.viewport.x +=(engine.events.initialX - x) / 10;
			engine.viewport.y += (engine.events.initialY - y) / 10;
			engine.map.draw();
			engine.events.initialX = x;
			engine.events.initialY = y;
			//engine.output("I'm draggin!");
		}
	},
	
	mouseDown : function(event){
		  event.preventDefault();
	      engine.events.isDragging = true;
		  var x = event.x;
		  var y = event.y;
		  	
		  var canvas = document.getElementById("canvas");
		
		  engine.events.initialX = x;
		  engine.events.initialY = y;
		 // engine.output("x:" + x + " y:" + y);
	},
	
	mouseUp : function(event) {
		  event.preventDefault();
	      engine.events.isDragging = false;
		  //engine.output("I'm not draggin!");
	}
		
};

engine.canvas.addEventListener("mousedown", engine.events.mouseDown, false);
engine.canvas.addEventListener("mouseup", engine.events.mouseUp, false);
engine.canvas.addEventListener("mousemove", engine.events.mouseMove, false);

engine.start = function(mapData, x, y)
{
   engine.canvas.onselectstart = function () { return false; }
   engine.output('starting...');
   engine.handle.translate(0, 8);
   engine.viewport.x = x;
   engine.viewport.y = y;
   engine.setMap(mapData);
   engine.map.draw();
   engine.output('done');
};



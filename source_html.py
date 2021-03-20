html_1 = '''<!doctype html>
<html lang="en">
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"
          integrity="sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMAS6/keqq/sMZMZ19scR4PsZChSR7A=="
          crossorigin=""/>
    <style>
        body{background-color: #3d85c6;}
        .mapid {
            height: 500px;
            width: 100%;
            margin: auto;
        }
        #title{
            background-color: #1c4587;
            padding-left: 10px;
            color: white;
        }
        #main{
            width: 900px;
            margin: auto;
        }
        #descr{
            background-color: #1c4587;
            padding: 5px;
            color: white;
            text-align: center;
            height:35px;
        }
        #myposition{
            font-style: oblique;
        }
        #plantPic{
            width: 100%;
        }
    </style>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"
            integrity="sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA=="
            crossorigin=""></script>'''
html_2 = f''' <title>Telegram bot</title>
    </head>
    <body>
     <div id="main">
         <div id="title">
             <h2>Telegram bot user #%d data visualization (click a city for the popup)</h2>
         </div>
        <div id="mapid" class="mapid"></div>
        <br>
        <div id="descr">
                <div id="text">Longitude, Latitude:</div>
                <div id="myposition"></div>
        </div>
    </div>
    <script>
        "use strict"
        var Source = %s;'''
html_3 = '''     
            var southWest = L.latLng(-90, -180),
            northEast = L.latLng(90, 180),
            bounds = L.latLngBounds(southWest, northEast);
        var map = L.map('mapid', {
            maxBounds: bounds,
            center: [0, 0],
            zoom: 1,
            minZoom: 1
        });
        map.on('mousemove', function(e){
            // console.log(e)
            let el =document.querySelector("#myposition")
            el.innerHTML = e.latlng.lng.toFixed(4) + ',  '+ e.latlng.lat.toFixed(4)
        })
        var CartoDB_Positron = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; ' +
                '<a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);
        var USGS_USImagery = L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 20,
            attribution: 'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
        });
        var Places = L.geoJSON(Source,{
            pointToLayer: function (feature, latlng) {
                return L.marker(latlng, {icon: L.icon({
                        iconUrl: 'https://freepngimg.com/thumb/star/16-star-png-image.png',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10],
                        popupAnchor: [0, -10]
                    })})
            },
            onEachFeature: function(feature, layer) {
                layer.bindPopup(`<p>City: ${feature.properties.city}<br>
            Current Date: ${feature.properties.date}<br>
            Temperature, Celsius: ${feature.properties.temp}</p>`);
            }
        }).addTo(map);
        var baseMaps = {
            "CartoDB": CartoDB_Positron,
            "Imagery": USGS_USImagery
        };
        var vectorL = {
            "Cities": Places
        };
        L.control.layers(baseMaps,vectorL).addTo(map);
        var count = 0
        var scbr = L.control.scale({imperial:false})
        map.addEventListener("zoomend",function (){
            if (map.getZoom() > 5 && count === 0){
                scbr.addTo(map);
                count ++;
            }
            else if (map.getZoom() <= 5) {
                scbr.remove();
                count = 0;
            }
        })
    </script>
</body>
</html>'''
Rickshaw.Graph.Axis.ExtendedTime = function(args) {

  var self = this;

  this.graph = args.graph;
  this.elements = [];
  this.ticksTreatment = args.ticksTreatment || 'plain';
  this.fixedTimeUnit = args.timeUnit;

  var time = new Rickshaw.Fixtures.Time();

  this.appropriateTimeUnit = function() {

    var unit;
    var units = time.units;

    var domain = this.graph.x.domain();
    var rangeSeconds = domain[1] - domain[0];

    units.forEach( function(u) {
      if (Math.floor(rangeSeconds / u.seconds) >= 2) {
        unit = unit || u;
      }
    } );

    return (unit || time.units[time.units.length - 1]);
  };

  this.tickOffsets = function() {

    var domain = this.graph.x.domain();

    var unit = this.fixedTimeUnit || this.appropriateTimeUnit();

    var tickSpacing = args.tickSpacing || unit.seconds;
    var count = Math.ceil((domain[1] - domain[0]) / tickSpacing);

    //console.log(count);

    var runningTick = domain[0];

    var offsets = [];

    for (var i = 0; i < count; i++) {

      var tickValue = time.ceil(runningTick, unit);
      runningTick = tickValue + tickSpacing;

      offsets.push( { value: tickValue, unit: unit } );
    }

    //console.log(offsets);

    return offsets;
  };

  this.render = function() {

    this.elements.forEach( function(e) {
      e.parentNode.removeChild(e);
    } );

    this.elements = [];

    var offsets = this.tickOffsets();

    offsets.forEach( function(o) {

      if (self.graph.x(o.value) > self.graph.x.range()[1]) return;

      var element = document.createElement('div');
      element.style.left = self.graph.x(o.value) + 'px';
      element.classList.add('x_tick');
      element.classList.add(self.ticksTreatment);

      var title = document.createElement('div');
      title.classList.add('title');
      title.innerHTML = o.unit.formatter(new Date(o.value * 1000));
      element.appendChild(title);

      self.graph.element.appendChild(element);
      self.elements.push(element);

    } );
  };

  this.graph.onUpdate( function() { self.render() } );
};
// ------------------------

// The new ExtendedX Axis:

Rickshaw.Graph.Axis.ExtendedY = function(args) {

  var self = this;
  var berthRate = 0.10;

  this.initialize = function(args) {

    this.graph = args.graph;
    this.orientation = args.orientation || 'right';

    var pixelsPerTick = args.pixelsPerTick || 75;
    this.ticks = args.ticks || Math.floor(this.graph.height / pixelsPerTick);
    this.tickSize = args.tickSize || 4;
    this.ticksTreatment = args.ticksTreatment || 'plain';

    this.tickSpacing = args.tickSpacing;

    if (args.element) {

      this.element = args.element;
      this.vis = d3.select(args.element)
          .append("svg:svg")
          .attr('class', 'rickshaw_graph y_axis');

      this.element = this.vis[0][0];
      this.element.style.position = 'relative';

      this.setSize({ width: args.width, height: args.height });

    } else {
      this.vis = this.graph.vis;
    }

    this.graph.onUpdate( function() { self.render() } );
  };

  this.setSize = function(args) {

    args = args || {};

    if (!this.element) return;

    if (typeof window !== 'undefined') {

      var style = window.getComputedStyle(this.element.parentNode, null);
      var elementWidth = parseInt(style.getPropertyValue('width'), 10);

      if (!args.auto) {
        var elementHeight = parseInt(style.getPropertyValue('height'), 10);
      }
    }

    this.width = args.width || elementWidth || this.graph.width * berthRate;
    this.height = args.height || elementHeight || this.graph.height;

    this.vis
        .attr('width', this.width)
        .attr('height', this.height * (1 + berthRate));

    var berth = this.height * berthRate;
    this.element.style.top = -1 * berth + 'px';
  };

  this.render = function() {

    if (this.graph.height !== this._renderHeight) this.setSize({ auto: true });

    var axis = d3.svg.axis().scale(this.graph.y).orient(this.orientation);

    if (this.tickSpacing) {
      var tickValues = [];

      var min = Math.ceil(axis.scale().domain()[0]/this.tickSpacing);
      var max = Math.floor(axis.scale().domain()[1]/this.tickSpacing);

      console.log("minmax", min,max);
      for (i = min * this.tickSpacing; i < max; i += 1) {
        console.log(i);
        tickValues.push(i * this.tickSpacing);
      }
      console.log(tickValues);
      axis.tickValues(tickValues);
    }

    axis.tickFormat( args.tickFormat || function(y) { return y } );

    if (this.orientation == 'left') {
      var berth = this.height * berthRate;
      var transform = 'translate(' + this.width + ', ' + berth + ')';
    }

    if (this.element) {
      this.vis.selectAll('*').remove();
    }

    this.vis
        .append("svg:g")
        .attr("class", ["y_ticks", this.ticksTreatment].join(" "))
        .attr("transform", transform)
        .call(axis.ticks(this.ticks).tickSubdivide(0).tickSize(this.tickSize));

    var gridSize = (this.orientation == 'right' ? 1 : -1) * this.graph.width;

    this.graph.vis
        .append("svg:g")
        .attr("class", "y_grid")
        .call(axis.ticks(this.ticks).tickSubdivide(0).tickSize(gridSize));

    this._renderHeight = this.graph.height;
  };

  this.initialize(args);
};

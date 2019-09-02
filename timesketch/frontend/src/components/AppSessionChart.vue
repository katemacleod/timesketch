<template>
    <div id="session-chart">
        <button @click="toggleChart">{{message}}</button>
        <ts-vega-lite-chart :vegaSpec="spec"></ts-vega-lite-chart>

        <div v-if="showChart">
            <p>Type of Session:</p>
            <select @change="selectType">
                <option v-for="session_type in session_types" :value=session_type v-bind:key="session_type">{{session_type}}</option>
            </select>
        </div>

        <div v-if="selectedSessions.length > 0"> 
            <p>Session ID:</p>
            <select @change="isolateSession">
                <option value="">-</option>
                <option v-for="session in selectedSessions" :value=session_type v-bind:key="session.session_type">{{session.id}}</option>
            </select>
        </div>

        <button v-if="showSessionButton" @click="showSession">Show Session</button>
    </div>
</template>

<script>
import TsVegaLiteChart from './VegaLiteChart'

export default {
  name: 'session-chart',
  components: {
      TsVegaLiteChart
  },

  data () {
      return {
          message: "Show Session Chart",
          showChart: false,
          showSessionButton: false,
          selectedSessions: [],
          sessions:  [
            {"start-time": 1, "end-time": 4, "session_type": "type1", "id": "1"},
            {"start-time": 2, "end-time": 4, "session_type": "type1", "id": "2"},
            {"start-time": 3, "end-time": 4, "session_type": "type1", "id": "4"},
            {"start-time": 2, "end-time": 5, "session_type": "type1", "id": "3"},
            {"start-time": 2, "end-time": 5, "session_type": "type2", "id": "1"},
            {"start-time": 9, "end-time": 11, "session_type": "type1", "id": "5"},
            {"start-time": 10, "end-time": 12, "session_type": "type1", "id": "6"},
            {"start-time": 7, "end-time": 8, "session_type": "type2", "id": "2"}
          ],
          spec: "{}",
          session_types: ["all"]
      }
  },

  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    eventList () {
      return this.$store.state
    }
  },

  methods: {
    toggleChart: function () {
        this.showChart = !this.showChart
        if (this.showChart) {
            this.message = "Hide Session Chart"
            this.getVegaSpec()
        }
        else {
            this.message = "Show Session Chart"
            this.showSessionButton = false
            this.selectedSessions = []
            this.spec = "{}"
            this.session_types = ["all"]
        }
        console.log(this.eventList)
    },

    selectType: function (event) {
        this.showSessionButton = false
        var dictSpec = JSON.parse(this.spec)
        if (event.target.options.selectedIndex == 0) {
            this.selectedSessions = []
            dictSpec['data']['values'] = this.sessions
        }
        else {
            var session_type = this.session_types[event.target.options.selectedIndex]
            this.selectedSessions = this.sessions.filter(session => session["session_type"] === session_type)
            dictSpec['data']['values'] = this.selectedSessions
        }
        this.spec = JSON.stringify(dictSpec)
    },

    showSession: function () {
        this.$store.commit('search', this.sketch.id)
    },

    isolateSession: function (event) {
        if (event.target.options.selectedIndex > 0) {
            this.showSessionButton = true
            var queryString = ''

            var selectedSessionsCopy = JSON.parse(JSON.stringify(this.selectedSessions))
            selectedSessionsCopy.forEach(function (session, index) {
                if (index == event.target.options.selectedIndex - 1) {
                    session["selected"] = true
                    queryString = "session.id." + session["session_type"] + ":" + session["id"]
                }
                else {
                    session["selected"] = false
                }
            })

            var dictSpec = JSON.parse(this.spec)
            dictSpec['data']['values'] = selectedSessionsCopy
            this.spec = JSON.stringify(dictSpec)

            this.$store.commit('updateCurrentQueryString', queryString)
        }
        else { this.showSessionButton = false }
    },

    getVegaSpec: function () {
        var dictSpec = { "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
                    "width": 900,
                    "height": 400,
                    "padding": 5,

                    "data": {
                        "values": this.sessions
                    },

                    "mark": "bar",

                    "selection": {
                        "highlight": {"type": "single", "empty": "none", "on": "mouseover"},
                        "select": {"type": "multi"}
                    },

                    "encoding": {
                        "y": {"field": "session_type", "type": "ordinal", "axis": {"title": "Session ID"}},
                        "x": {"field": "start-time", "type": "quantitative", "axis": {"title": "Timestamp", "tickCount": 10}},
                        "x2": {"field":"end-time"},
                        "color": {
                            "field": "id", "type": "nominal",
                            "scale": {"scheme": "tableau10"},
                            "legend": false
                        },
                        "opacity": {
                            "condition": [
                                {"test":"datum.selected == true", "value": 1}, 
                                {"test":"datum.selected == false", "value": 0.2}
                            ],
                            "value": 0.7
                        }
                    }
                    
                }
        this.session_types.push("type1")
        this.session_types.push("type2")
        this.spec = JSON.stringify(dictSpec)
    }
  }
}
</script>

<style lang="scss"></style>
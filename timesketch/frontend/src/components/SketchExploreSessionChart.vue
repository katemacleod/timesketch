<template>
    <div>
        <ts-vega-lite-chart :vegaSpec="spec"></ts-vega-lite-chart>
        <div class="field">
            <button class="button" @click="toggleChart" :disabled="sessions.length === 0 && showChart === false">{{message}}</button>
        </div>

        <div class="field" v-if="showChart">
            <label class="label">Type of Session:</label>
            <div class="control">
                <div class="select">
                    <select v-model="selectedType" @change="selectSessionType">
                        <option disabled value="">Please select one</option>
                        <option v-for="session_type in sessionTypes" :value=session_type v-bind:key="session_type">{{session_type}}</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="field" v-if="selectedSessions.length > 0"> 
            <label class="label">Session ID:</label>
            <div class="control">
                <div class="select">
                    <select v-model="selectedID" @change="selectSessionID">
                        <option disabled value="">Please select one</option>
                        <option v-for="session in selectedSessions" :value=session.session_id v-bind:key="session.session_type + session.session_id">{{session.session_id}}</option>
                    </select>
                </div>
            </div>
        </div>
   </div>
</template>

<script>
import TsVegaLiteChart from './VegaLiteChart'

export default {
  name: 'ts-explore-session-chart',
  components: {
        TsVegaLiteChart
  },

  data () {
      return {
            roundedSessions: [],
            message: 'Show Session Chart',
            showChart: false,
            selectedSessions: [],
            spec: '{}',
            sessionTypes: ['all'],
            barSize: 0,
            smallestTimestamp: 0,
            selectedType: '',
            selectedID: '',
            prevQueryString: ''
      }
  },

  computed: {
    sketch () {
        return this.$store.state.sketch
    },
    sessions () {
        return this.$store.state.meta.sessions
    }
  },

  methods: {
    toggleChart: function () {
        this.showChart = !this.showChart
        if (this.showChart) {
            this.message = 'Hide Session Chart'
            this.getVegaSpec()
        }
        else {
            this.message = 'Show Session Chart'
            this.selectedSessions = []
            this.spec = '{}'
            this.sessionTypes = ['all']
            this.selectedType = ''
            this.selectedID = ''

        this.$store.commit('updateCurrentQueryString', this.prevQueryString)
        this.$store.commit('search', this.sketch.id)
        }
    },

    selectSessionType: function (event) {
        this.selectedID = ''
        var dictSpec = JSON.parse(this.spec)
        if (this.selectedType === 'all') {
            this.selectedSessions = []
            dictSpec['data']['values'] = this.roundedSessions
        }
        else {
            this.selectedSessions = this.roundedSessions.filter(session => session['session_type'] === this.selectedType)
            dictSpec['data']['values'] = this.selectedSessions
        }
        dictSpec['vconcat'][1]['selection']['brush']['init']['x'] = [this.smallestTimestamp, this.smallestTimestamp + (this.barSize * 50)]
        this.spec = JSON.stringify(dictSpec)
    },

    selectSessionID: function (event) {
        var queryString = ''
        var selection = []

        var selectedSessionsCopy = JSON.parse(JSON.stringify(this.selectedSessions))
        for (var i = 0; i < selectedSessionsCopy.length; i++) {
            var session = selectedSessionsCopy[i]
            if (this.selectedType === session.session_type && this.selectedID === session.session_id) {
                session['selected'] = true
                queryString = 'session_id.' + session['session_type'] + ':' + session['session_id']
                selection = [session['start_timestamp'] - (this.barSize * 5), session['end_timestamp'] + (this.barSize * 5)]
            }
            else {
                session['selected'] = false
            }
        }

        var dictSpec = JSON.parse(this.spec)
        dictSpec['data']['values'] = selectedSessionsCopy
        dictSpec['vconcat'][1]['selection']['brush']['init']['x'] = selection
        this.spec = JSON.stringify(dictSpec)

        this.$store.commit('updateCurrentQueryString', queryString)
        this.$store.commit('search', this.sketch.id)
    },

    getRoundedSessions: function () {
        //increases the visibility of sessions when plotted
        var roundedSessions = JSON.parse(JSON.stringify(this.sessions))
        var smallestTimestamp = roundedSessions[0].start_timestamp
        var largest_timestamp = roundedSessions[0].end_timestamp
        for (var i = 1; i < roundedSessions.length; i++) {
            if (roundedSessions[i].start_timestamp < smallestTimestamp) {
                smallestTimestamp = roundedSessions[i].start_timestamp
            }
            if (roundedSessions[i].end_timestamp > largest_timestamp) {
                largest_timestamp = roundedSessions[i].end_timestamp
            }
        }
        var timeRange = (largest_timestamp - smallestTimestamp)

        //session bars will take up 1/1000th of the chart if they would otherwise be smaller
        this.barSize = Math.round(timeRange / 1000)
        this.smallestTimestamp = smallestTimestamp

        for (var i = 0; i < roundedSessions.length; i++) {
            var session = roundedSessions[i]
            var extended_end = session.start_timestamp + this.barSize
            if (session.end_timestamp < extended_end) {
                session.end_timestamp = extended_end
            }

            //do not display sessions as overlapping if they are not actually
            if (i !== 0 &&
                roundedSessions[i - 1].session_type === session.session_type &&
                roundedSessions[i - 1].end_timestamp > session.start_timestamp &&
                roundedSessions[i - 1].start_timestamp !== session.start_timestamp) {

                var real_end = this.sessions[i-1].end_timestamp
                if (real_end <= session.start_timestamp) {
                    roundedSessions[i - 1].end_timestamp = session.start_timestamp
                }
                else {
                    roundedSessions[i - 1].end_timestamp = real_end
                }
            }
        }
        this.roundedSessions = roundedSessions
    },

    getVegaSpec: function () {
        this.prevQueryString = this.$store.state.currentQueryString
        this.getRoundedSessions()
        var dictSpec = { "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
            "data": {
                "values": this.roundedSessions
            },
            "vconcat": [{
                "width": 900,
                "height": 400,
                "padding": 5,

                "mark": "bar",

                "encoding": {
                    "y": {"field": "session_type", "type": "ordinal", "axis": {"title": "Session Type"}},
                    "x": {"field": "start_timestamp", "type": "quantitative", "axis": {"title": "Timestamp", "tickCount": 5}, "scale": {"domain": {"selection": "brush"}}},
                    "x2": {"field":"end_timestamp"},
                    "color": {
                        "field": "session_id", "type": "nominal",
                        "scale": {"scheme": "tableau20"},
                        "legend": false
                    },
                    "opacity": {
                        "condition": [
                            {"test":"datum.selected == true", "value": 1}, 
                            {"test":"datum.selected == false", "value": 0.2}
                        ],
                        "value": 0.8
                    }
                }
            }, {
                "width": 900,
                "height": 100,
                "padding": 5,

                "selection": {
                    "brush": {
                        "type": "interval",
                        "encodings": ["x"],
                        "init": {"x": [this.smallestTimestamp, this.smallestTimestamp + (this.barSize * 50)]}
                    }
                },

                "mark": {"type": "point", "size": 200},

                "encoding": {
                    "y": {"field": "session_type", "type": "ordinal", "axis": {"title": "Session Type"}},
                    "x": {"field": "start_timestamp", "type": "quantitative", "axis": {"title": "Timestamp", "tickCount": 5}, "scale": { "zero": false}},
                    "color": {
                        "field": "session_id", "type": "nominal",
                        "scale": {"scheme": "tableau20"},
                        "legend": false
                    },
                    "opacity": {
                        "condition": [
                            {"test":"datum.selected == true", "value": 1}, 
                            {"test":"datum.selected == false", "value": 0.2}
                        ],
                        "value": 0.8
                    }
                }
            }]
        }
        this.sessionTypes = this.sessionTypes.concat([...new Set(this.sessions.map(s => s.session_type))])
        this.spec = JSON.stringify(dictSpec)
    }
  }
}
</script>

<style lang="scss"></style>
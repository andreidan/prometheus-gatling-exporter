===========================
prometheus-gatling-exporter
===========================

This exporter parses the output of the Gatling (v2.3.1) ``simulation.log`` file.
It will report the response time for every operation under the
``loadgenerator`` metric using the ``status`` (which can be ``Success`` or
``Failure``), ``sim_id`` (indicating the simulation that's being executed) and
for the failed operations the ``error`` (containing the details around the
failure reason) labels.
A ``loadgenerator_summary`` metric is also generated and it reports the number
of successful and failed executed statements.

Example::

    # HELP loadgenerator loadgenerator statements response time
    # TYPE loadgenerator gauge
    loadgenerator{status="Success",sim_id="Select_GroupBy_StrShort"} 4.0
    # HELP loadgenerator loadgenerator statements response time
    # TYPE loadgenerator gauge
    loadgenerator{status="Success",sim_id="Select_GroupBy_StrShort"} 3.0
    # HELP loadgenerator loadgenerator statements response time
    # TYPE loadgenerator gauge
    loadgenerator{status="Success",sim_id="Select_GroupBy_StrShort"} 3.0
    # HELP loadgenerator loadgenerator statements response time
    # TYPE loadgenerator gauge
    loadgenerator{status="Success",sim_id="Insert"} 29.0
    # HELP loadgenerator loadgenerator statements response time
    # TYPE loadgenerator gauge
    loadgenerator{status="Success",sim_id="Select_GroupBy_StrShort"} 2.0
    # HELP loadgenerator_summary
    # TYPE loadgenerator_summary gauge
    loadgenerator_summary{status="Success",sim_id="Insert"} 91.0
    # HELP loadgenerator_summary
    # TYPE loadgenerator_summary gauge
    loadgenerator_summary{status="Failure",sim_id="Insert"} 0.0
    # HELP loadgenerator_summary
    # TYPE loadgenerator_summary gauge
    loadgenerator_summary{status="Success",sim_id="Select_GroupBy_StrShort"} 272.0
    # HELP loadgenerator_summary
    # TYPE loadgenerator_summary gauge
    loadgenerator_summary{status="Failure",sim_id="Select_GroupBy_StrShort"} 0.0


Usage
=====
Prometheus ingests new metrics by scraping http endpoints. The gatling exporter
will start a http server (default port is ``9102``) for prometheus to scrape.
When the exporter is started it will start processing the *new entries* in the
simulation log file (``tail -f``), and store them in an internal buffer (the
length of the buffer is configurable using ``--buffer_len`` and defaults to
``30_000``) until prometheus scrapes them.
Old entries in the buffer will be replaced by new simulation entries if the
metrics are not scraped for a long enough time, in order to respect the
configured buffer length.

In order to start the exporter you'll need to provide the path towards the
gatling simulation file using ``-s`` Eg.

``python gatling_exporter.py -s /opt/gatling-charts-highcharts-bundle-2.3.1/results/cratedb-1532095744058/simulation.log``

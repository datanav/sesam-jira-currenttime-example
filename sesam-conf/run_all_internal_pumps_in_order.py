import ijson.common
import sesamclient

with sesamclient.Connection("http://localhost:9042/api") as connection:

    pipe_ids = [pipe.id for pipe in connection.get_pipes()]
    pipe_ids.sort()
    print ("Running pumps...")
    for pipe_id in pipe_ids:
        if "step" in pipe_id or "cooked" in pipe_id or "workentries" in pipe_id:

            if pipe_id in [
                "workentry-currenttime"
             ]:
                # skip this pipe
                continue

            # this looks like an internal pipe
            pump = connection.get_pipe(pipe_id).get_pump()
            if "update-last-seen" in pump.supported_operations:
                print("  '%s'" % (pipe_id,))
                pump.wait_for_pump_to_finish_running()
                pump.unset_last_seen()
                pump.start()
                pump.wait_for_pump_to_finish_running()

                dataset = connection.get_dataset(pipe_id)
                try:
                    dataset.wait_for_indexes_to_finish_updating()
                except ijson.common.IncompleteJSONError as e:
                    print ("    dataset.wait_for_indexes_to_finish_updating() failed: %s" % (e,))

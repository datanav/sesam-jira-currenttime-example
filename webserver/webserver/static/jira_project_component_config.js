/**
 * Created by knut.johannessen on 21.10.16.
 */




$(document).ready(function() {
  var busyIndicator = $("#busyIndicator");

  $(document).ajaxStart(function() {
    busyIndicator.show();
  });

  $(document).ajaxStop(function() {
    busyIndicator.hide();
  });

  function registerResultGUIHandlers() {
    $("button.delete-mapping").click(function() {
      var button = $(this);
      var mappingId = button.data("mapping_id");
      if (confirm("Are you sure you want to delete this mapping?")) {
        $.post("jira-project-component-config", {"delete": "1", "mapping_id": mappingId}, function(data) {
          handleResultMappings(data);
        });
      }
    });
  }

  function handleResultMappings(data) {
    $("#jira-project-component-mappings").html(data);
    registerResultGUIHandlers();
  }


  var jiraProjectSelect =  $('[name=jira-project]');
  var jiraComponentSelect =  $('[name=jira-component]');
  var jiraComponentSelect_parent =  $('#jira-component-parent');

  var currenttimeProjectSelect =  $('[name=currenttime-project]');
  var currenttimeTaskSelect =  $('[name=currenttime-task]');
  var currenttimeSubtaskSelect =  $('[name=currenttime-subtask]');


  var addMappingForm = $("#add-mapping-form");
  var addMappingButton = $("#add-mapping-button");

  // Attach a submit handler to the form
  addMappingForm.submit(function( event ) {

    // Stop form from submitting normally
    event.preventDefault();

    // Get some values from elements on the page:
    var formDataAsString = addMappingForm.serialize();

    $.post("jira-project-component-config", formDataAsString, function(data) {
      handleResultMappings(data);
    });

  });

  registerResultGUIHandlers();

  function updateDependantGUIState() {
    var disable_button = false;

    var jira_project_id = jiraProjectSelect.val();

    var ct_project_id = currenttimeProjectSelect.val();
    var ct_task_id = currenttimeTaskSelect.val();
    var ct_subtask_id = currenttimeSubtaskSelect.val();


    if (jira_project_id === null || jira_project_id === "0"
        || ct_project_id === null || ct_project_id === "0"
      || ct_task_id === null || ct_task_id === "0"
      || ct_subtask_id === null || ct_subtask_id === "0") {
      disable_button = true;
    }

    addMappingButton.prop('disabled', disable_button);

    // hide the component selectbox if it is empty
    if (jiraComponentSelect.has('option').length > 0) {
      jiraComponentSelect_parent.show();
    } else {
      jiraComponentSelect_parent.hide();
    }
  }


  $.each(currenttimeProjects, function() {
    var option = $('<option />');
    option.val(this.id);
    option.text(this.name);
    option.data('project', this);
      currenttimeProjectSelect.append(option);
  });

  currenttimeProjectSelect.change(function() {
    var option = currenttimeProjectSelect.find(':selected');
    var project = option.data('project');

    currenttimeTaskSelect.empty();
    $.each(project.tasks, function() {
      var option = $('<option />');
      option.val(this.id);
      option.text(this.name);
      option.data('task', this);
        currenttimeTaskSelect.append(option);
    });

    currenttimeSubtaskSelect.empty();
    updateDependantGUIState();
  });


  currenttimeTaskSelect.change(function() {
    var option = currenttimeTaskSelect.find(':selected');
    var task = option.data('task');

    currenttimeSubtaskSelect.empty();
    $.each(task.subtasks, function() {
      var option = $('<option />');
      option.val(this.id);
      option.text(this.name);
      option.data('subtask', this);
        currenttimeSubtaskSelect.append(option);
    });
    updateDependantGUIState();
  });

  currenttimeSubtaskSelect.change(function() {
    updateDependantGUIState();
  });


  $.each(jiraProjects, function() {
    var option = $('<option />');
    option.val(this.id);
    option.text(this.name);
    option.data('project', this);
      jiraProjectSelect.append(option);
  });

  jiraProjectSelect.change(function() {
    var option_element = jiraProjectSelect.find(':selected');
    var project = option_element.data('project');

    jiraComponentSelect.empty();
    $.each(project.components, function() {
      var option = $('<option />');
      option.val(this.id);
      option.text(this.name);
      option.data('option', this);
        jiraComponentSelect.append(option);
    });

    updateDependantGUIState();
  });


  jiraComponentSelect.change(function() {
    updateDependantGUIState();
  });

  updateDependantGUIState();
});
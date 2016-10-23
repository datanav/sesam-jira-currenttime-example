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
        $.post("customfieldvalue-config", {"delete": "1", "mapping_id": mappingId}, function(data) {
          handleResultMappings(data);
        });
      }
    });
  }

  function handleResultMappings(data) {
    $("#customfieldvalue-mappings").html(data);
    registerResultGUIHandlers();
  }


  var currenttimeProjectSelect =  $('[name=currenttime-project]');
  var currenttimeTaskSelect =  $('[name=currenttime-task]');
  var currenttimeSubtaskSelect =  $('[name=currenttime-subtask]');

  var jiraCustomfieldSelect =  $('[name=jira-customfield]');
  var jiraCustomfieldOptionSelect =  $('[name=jira-customfield-option]');
  var jiraCustomfieldSuboptionSelect =  $('[name=jira-customfield-suboption]');
  var jiraCustomfieldSuboptionSelect_parent =  $('#jira-customfield-suboption-parent');

  var addMappingForm = $("#add-mapping-form");
  var addMappingButton = $("#add-mapping-button");

  // Attach a submit handler to the form
  addMappingForm.submit(function( event ) {

    // Stop form from submitting normally
    event.preventDefault();

    // Get some values from elements on the page:
    var formDataAsString = addMappingForm.serialize();

    $.post("customfieldvalue-config", formDataAsString, function(data) {
      handleResultMappings(data);
    });

  });

  registerResultGUIHandlers();

  function updateDependantGUIState() {
    var disable_button = false;

    var jira_customfield_id = jiraCustomfieldSelect.val();
    var jira_customfield_option_id = jiraCustomfieldOptionSelect.val();

    var ct_project_id = currenttimeProjectSelect.val();
    var ct_task_id = currenttimeTaskSelect.val();
    var ct_subtask_id = currenttimeSubtaskSelect.val();


    if (jira_customfield_id === null || jira_customfield_id === "0"
        || jira_customfield_option_id === null || jira_customfield_option_id === "0"
        || ct_project_id === null || ct_project_id === "0"
      || ct_task_id === null || ct_task_id === "0"
      || ct_subtask_id === null || ct_subtask_id === "0") {
      //disable_button = true;
    }

    addMappingButton.prop('disabled', disable_button);

    // hide the sub-options selectbox if it is empty (which it often is)
    if (jiraCustomfieldSuboptionSelect.has('option').length > 0) {
      jiraCustomfieldSuboptionSelect_parent.show();
    } else {
      jiraCustomfieldSuboptionSelect_parent.hide();
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


  $.each(jiraCustomfields, function() {
    var option = $('<option />');
    option.val(this.id);
    option.text(this.name);
    option.data('customfield', this);
      jiraCustomfieldSelect.append(option);
  });

  jiraCustomfieldSelect.change(function() {
    var option_element = jiraCustomfieldSelect.find(':selected');
    var customfield = option_element.data('customfield');

    jiraCustomfieldOptionSelect.empty();
    $.each(customfield.options, function() {
      var option = $('<option />');
      option.val(this.id);
      option.text(this.name);
      option.data('option', this);
        jiraCustomfieldOptionSelect.append(option);
    });

    jiraCustomfieldSuboptionSelect.empty();
    updateDependantGUIState();
  });


  jiraCustomfieldOptionSelect.change(function() {
    var option_element = jiraCustomfieldOptionSelect.find(':selected');
    var option = option_element.data('option');

    jiraCustomfieldSuboptionSelect.empty();
    $.each(option.suboptions, function() {
      var option = $('<option />');
      option.val(this.id);
      option.text(this.name);
      option.data('suboption', this);
        jiraCustomfieldSuboptionSelect.append(option);
    });

    updateDependantGUIState();
  });

  jiraCustomfieldSuboptionSelect.change(function() {
    updateDependantGUIState();
  });


  updateDependantGUIState();
});
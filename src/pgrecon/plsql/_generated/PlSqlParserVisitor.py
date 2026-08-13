# Generated from PlSqlParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .PlSqlParser import PlSqlParser
else:
    from PlSqlParser import PlSqlParser

# This class defines a complete generic visitor for a parse tree produced by PlSqlParser.

class PlSqlParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by PlSqlParser#sql_script.
    def visitSql_script(self, ctx:PlSqlParser.Sql_scriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unit_statement.
    def visitUnit_statement(self, ctx:PlSqlParser.Unit_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_diskgroup.
    def visitAlter_diskgroup(self, ctx:PlSqlParser.Alter_diskgroupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_disk_clause.
    def visitAdd_disk_clause(self, ctx:PlSqlParser.Add_disk_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_disk_clause.
    def visitDrop_disk_clause(self, ctx:PlSqlParser.Drop_disk_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#resize_disk_clause.
    def visitResize_disk_clause(self, ctx:PlSqlParser.Resize_disk_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#replace_disk_clause.
    def visitReplace_disk_clause(self, ctx:PlSqlParser.Replace_disk_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#wait_nowait.
    def visitWait_nowait(self, ctx:PlSqlParser.Wait_nowaitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rename_disk_clause.
    def visitRename_disk_clause(self, ctx:PlSqlParser.Rename_disk_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#disk_online_clause.
    def visitDisk_online_clause(self, ctx:PlSqlParser.Disk_online_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#disk_offline_clause.
    def visitDisk_offline_clause(self, ctx:PlSqlParser.Disk_offline_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#timeout_clause.
    def visitTimeout_clause(self, ctx:PlSqlParser.Timeout_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rebalance_diskgroup_clause.
    def visitRebalance_diskgroup_clause(self, ctx:PlSqlParser.Rebalance_diskgroup_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#phase.
    def visitPhase(self, ctx:PlSqlParser.PhaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#check_diskgroup_clause.
    def visitCheck_diskgroup_clause(self, ctx:PlSqlParser.Check_diskgroup_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#diskgroup_template_clauses.
    def visitDiskgroup_template_clauses(self, ctx:PlSqlParser.Diskgroup_template_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#qualified_template_clause.
    def visitQualified_template_clause(self, ctx:PlSqlParser.Qualified_template_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#redundancy_clause.
    def visitRedundancy_clause(self, ctx:PlSqlParser.Redundancy_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#striping_clause.
    def visitStriping_clause(self, ctx:PlSqlParser.Striping_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#force_noforce.
    def visitForce_noforce(self, ctx:PlSqlParser.Force_noforceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#diskgroup_directory_clauses.
    def visitDiskgroup_directory_clauses(self, ctx:PlSqlParser.Diskgroup_directory_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dir_name.
    def visitDir_name(self, ctx:PlSqlParser.Dir_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#diskgroup_alias_clauses.
    def visitDiskgroup_alias_clauses(self, ctx:PlSqlParser.Diskgroup_alias_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#diskgroup_volume_clauses.
    def visitDiskgroup_volume_clauses(self, ctx:PlSqlParser.Diskgroup_volume_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_volume_clause.
    def visitAdd_volume_clause(self, ctx:PlSqlParser.Add_volume_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_volume_clause.
    def visitModify_volume_clause(self, ctx:PlSqlParser.Modify_volume_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#diskgroup_attributes.
    def visitDiskgroup_attributes(self, ctx:PlSqlParser.Diskgroup_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_diskgroup_file_clause.
    def visitDrop_diskgroup_file_clause(self, ctx:PlSqlParser.Drop_diskgroup_file_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#convert_redundancy_clause.
    def visitConvert_redundancy_clause(self, ctx:PlSqlParser.Convert_redundancy_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#usergroup_clauses.
    def visitUsergroup_clauses(self, ctx:PlSqlParser.Usergroup_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#user_clauses.
    def visitUser_clauses(self, ctx:PlSqlParser.User_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#file_permissions_clause.
    def visitFile_permissions_clause(self, ctx:PlSqlParser.File_permissions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#file_owner_clause.
    def visitFile_owner_clause(self, ctx:PlSqlParser.File_owner_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#scrub_clause.
    def visitScrub_clause(self, ctx:PlSqlParser.Scrub_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#quotagroup_clauses.
    def visitQuotagroup_clauses(self, ctx:PlSqlParser.Quotagroup_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#property_name.
    def visitProperty_name(self, ctx:PlSqlParser.Property_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#property_value.
    def visitProperty_value(self, ctx:PlSqlParser.Property_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#filegroup_clauses.
    def visitFilegroup_clauses(self, ctx:PlSqlParser.Filegroup_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_filegroup_clause.
    def visitAdd_filegroup_clause(self, ctx:PlSqlParser.Add_filegroup_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_filegroup_clause.
    def visitModify_filegroup_clause(self, ctx:PlSqlParser.Modify_filegroup_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#move_to_filegroup_clause.
    def visitMove_to_filegroup_clause(self, ctx:PlSqlParser.Move_to_filegroup_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_filegroup_clause.
    def visitDrop_filegroup_clause(self, ctx:PlSqlParser.Drop_filegroup_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#quorum_regular.
    def visitQuorum_regular(self, ctx:PlSqlParser.Quorum_regularContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#undrop_disk_clause.
    def visitUndrop_disk_clause(self, ctx:PlSqlParser.Undrop_disk_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#diskgroup_availability.
    def visitDiskgroup_availability(self, ctx:PlSqlParser.Diskgroup_availabilityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#enable_disable_volume.
    def visitEnable_disable_volume(self, ctx:PlSqlParser.Enable_disable_volumeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_function.
    def visitDrop_function(self, ctx:PlSqlParser.Drop_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_flashback_archive.
    def visitAlter_flashback_archive(self, ctx:PlSqlParser.Alter_flashback_archiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_hierarchy.
    def visitAlter_hierarchy(self, ctx:PlSqlParser.Alter_hierarchyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_function.
    def visitAlter_function(self, ctx:PlSqlParser.Alter_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_java.
    def visitAlter_java(self, ctx:PlSqlParser.Alter_javaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#match_string.
    def visitMatch_string(self, ctx:PlSqlParser.Match_stringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_function_body.
    def visitCreate_function_body(self, ctx:PlSqlParser.Create_function_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sql_macro_body.
    def visitSql_macro_body(self, ctx:PlSqlParser.Sql_macro_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#parallel_enable_clause.
    def visitParallel_enable_clause(self, ctx:PlSqlParser.Parallel_enable_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partition_by_clause.
    def visitPartition_by_clause(self, ctx:PlSqlParser.Partition_by_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#result_cache_clause.
    def visitResult_cache_clause(self, ctx:PlSqlParser.Result_cache_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#accessible_by_clause.
    def visitAccessible_by_clause(self, ctx:PlSqlParser.Accessible_by_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_collation_clause.
    def visitDefault_collation_clause(self, ctx:PlSqlParser.Default_collation_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#aggregate_clause.
    def visitAggregate_clause(self, ctx:PlSqlParser.Aggregate_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pipelined_using_clause.
    def visitPipelined_using_clause(self, ctx:PlSqlParser.Pipelined_using_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#accessor.
    def visitAccessor(self, ctx:PlSqlParser.AccessorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#relies_on_part.
    def visitRelies_on_part(self, ctx:PlSqlParser.Relies_on_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#streaming_clause.
    def visitStreaming_clause(self, ctx:PlSqlParser.Streaming_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_outline.
    def visitAlter_outline(self, ctx:PlSqlParser.Alter_outlineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#outline_options.
    def visitOutline_options(self, ctx:PlSqlParser.Outline_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_lockdown_profile.
    def visitAlter_lockdown_profile(self, ctx:PlSqlParser.Alter_lockdown_profileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lockdown_feature.
    def visitLockdown_feature(self, ctx:PlSqlParser.Lockdown_featureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lockdown_options.
    def visitLockdown_options(self, ctx:PlSqlParser.Lockdown_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lockdown_statements.
    def visitLockdown_statements(self, ctx:PlSqlParser.Lockdown_statementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#statement_clauses.
    def visitStatement_clauses(self, ctx:PlSqlParser.Statement_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#clause_options.
    def visitClause_options(self, ctx:PlSqlParser.Clause_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#option_values.
    def visitOption_values(self, ctx:PlSqlParser.Option_valuesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#string_list.
    def visitString_list(self, ctx:PlSqlParser.String_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#disable_enable.
    def visitDisable_enable(self, ctx:PlSqlParser.Disable_enableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_lockdown_profile.
    def visitDrop_lockdown_profile(self, ctx:PlSqlParser.Drop_lockdown_profileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_package.
    def visitDrop_package(self, ctx:PlSqlParser.Drop_packageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_package.
    def visitAlter_package(self, ctx:PlSqlParser.Alter_packageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_package.
    def visitCreate_package(self, ctx:PlSqlParser.Create_packageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_package_body.
    def visitCreate_package_body(self, ctx:PlSqlParser.Create_package_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#package_obj_spec.
    def visitPackage_obj_spec(self, ctx:PlSqlParser.Package_obj_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#procedure_spec.
    def visitProcedure_spec(self, ctx:PlSqlParser.Procedure_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#function_spec.
    def visitFunction_spec(self, ctx:PlSqlParser.Function_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#package_obj_body.
    def visitPackage_obj_body(self, ctx:PlSqlParser.Package_obj_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_pmem_filestore.
    def visitAlter_pmem_filestore(self, ctx:PlSqlParser.Alter_pmem_filestoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_pmem_filestore.
    def visitDrop_pmem_filestore(self, ctx:PlSqlParser.Drop_pmem_filestoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_procedure.
    def visitDrop_procedure(self, ctx:PlSqlParser.Drop_procedureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_procedure.
    def visitAlter_procedure(self, ctx:PlSqlParser.Alter_procedureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#function_body.
    def visitFunction_body(self, ctx:PlSqlParser.Function_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#procedure_body.
    def visitProcedure_body(self, ctx:PlSqlParser.Procedure_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_procedure_body.
    def visitCreate_procedure_body(self, ctx:PlSqlParser.Create_procedure_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_resource_cost.
    def visitAlter_resource_cost(self, ctx:PlSqlParser.Alter_resource_costContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_outline.
    def visitDrop_outline(self, ctx:PlSqlParser.Drop_outlineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_rollback_segment.
    def visitAlter_rollback_segment(self, ctx:PlSqlParser.Alter_rollback_segmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_restore_point.
    def visitDrop_restore_point(self, ctx:PlSqlParser.Drop_restore_pointContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_rollback_segment.
    def visitDrop_rollback_segment(self, ctx:PlSqlParser.Drop_rollback_segmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_role.
    def visitDrop_role(self, ctx:PlSqlParser.Drop_roleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_pmem_filestore.
    def visitCreate_pmem_filestore(self, ctx:PlSqlParser.Create_pmem_filestoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pmem_filestore_options.
    def visitPmem_filestore_options(self, ctx:PlSqlParser.Pmem_filestore_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#file_path.
    def visitFile_path(self, ctx:PlSqlParser.File_pathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_rollback_segment.
    def visitCreate_rollback_segment(self, ctx:PlSqlParser.Create_rollback_segmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_trigger.
    def visitDrop_trigger(self, ctx:PlSqlParser.Drop_triggerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_trigger.
    def visitAlter_trigger(self, ctx:PlSqlParser.Alter_triggerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_trigger.
    def visitCreate_trigger(self, ctx:PlSqlParser.Create_triggerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#trigger_follows_clause.
    def visitTrigger_follows_clause(self, ctx:PlSqlParser.Trigger_follows_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#trigger_when_clause.
    def visitTrigger_when_clause(self, ctx:PlSqlParser.Trigger_when_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#simple_dml_trigger.
    def visitSimple_dml_trigger(self, ctx:PlSqlParser.Simple_dml_triggerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#for_each_row.
    def visitFor_each_row(self, ctx:PlSqlParser.For_each_rowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#compound_dml_trigger.
    def visitCompound_dml_trigger(self, ctx:PlSqlParser.Compound_dml_triggerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#non_dml_trigger.
    def visitNon_dml_trigger(self, ctx:PlSqlParser.Non_dml_triggerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#trigger_body.
    def visitTrigger_body(self, ctx:PlSqlParser.Trigger_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#compound_trigger_block.
    def visitCompound_trigger_block(self, ctx:PlSqlParser.Compound_trigger_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#timing_point_section.
    def visitTiming_point_section(self, ctx:PlSqlParser.Timing_point_sectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#non_dml_event.
    def visitNon_dml_event(self, ctx:PlSqlParser.Non_dml_eventContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dml_event_clause.
    def visitDml_event_clause(self, ctx:PlSqlParser.Dml_event_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dml_event_element.
    def visitDml_event_element(self, ctx:PlSqlParser.Dml_event_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dml_event_nested_clause.
    def visitDml_event_nested_clause(self, ctx:PlSqlParser.Dml_event_nested_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#referencing_clause.
    def visitReferencing_clause(self, ctx:PlSqlParser.Referencing_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#referencing_element.
    def visitReferencing_element(self, ctx:PlSqlParser.Referencing_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_type.
    def visitDrop_type(self, ctx:PlSqlParser.Drop_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_type.
    def visitAlter_type(self, ctx:PlSqlParser.Alter_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#compile_type_clause.
    def visitCompile_type_clause(self, ctx:PlSqlParser.Compile_type_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#replace_type_clause.
    def visitReplace_type_clause(self, ctx:PlSqlParser.Replace_type_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_method_spec.
    def visitAlter_method_spec(self, ctx:PlSqlParser.Alter_method_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_method_element.
    def visitAlter_method_element(self, ctx:PlSqlParser.Alter_method_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_collection_clauses.
    def visitAlter_collection_clauses(self, ctx:PlSqlParser.Alter_collection_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dependent_handling_clause.
    def visitDependent_handling_clause(self, ctx:PlSqlParser.Dependent_handling_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dependent_exceptions_part.
    def visitDependent_exceptions_part(self, ctx:PlSqlParser.Dependent_exceptions_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_type.
    def visitCreate_type(self, ctx:PlSqlParser.Create_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_definition.
    def visitType_definition(self, ctx:PlSqlParser.Type_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_type_def.
    def visitObject_type_def(self, ctx:PlSqlParser.Object_type_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_as_part.
    def visitObject_as_part(self, ctx:PlSqlParser.Object_as_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_under_part.
    def visitObject_under_part(self, ctx:PlSqlParser.Object_under_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#nested_table_type_def.
    def visitNested_table_type_def(self, ctx:PlSqlParser.Nested_table_type_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sqlj_object_type.
    def visitSqlj_object_type(self, ctx:PlSqlParser.Sqlj_object_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_body.
    def visitType_body(self, ctx:PlSqlParser.Type_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_body_elements.
    def visitType_body_elements(self, ctx:PlSqlParser.Type_body_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#map_order_func_declaration.
    def visitMap_order_func_declaration(self, ctx:PlSqlParser.Map_order_func_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subprog_decl_in_type.
    def visitSubprog_decl_in_type(self, ctx:PlSqlParser.Subprog_decl_in_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#proc_decl_in_type.
    def visitProc_decl_in_type(self, ctx:PlSqlParser.Proc_decl_in_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#func_decl_in_type.
    def visitFunc_decl_in_type(self, ctx:PlSqlParser.Func_decl_in_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#constructor_declaration.
    def visitConstructor_declaration(self, ctx:PlSqlParser.Constructor_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modifier_clause.
    def visitModifier_clause(self, ctx:PlSqlParser.Modifier_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_member_spec.
    def visitObject_member_spec(self, ctx:PlSqlParser.Object_member_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sqlj_object_type_attr.
    def visitSqlj_object_type_attr(self, ctx:PlSqlParser.Sqlj_object_type_attrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#element_spec.
    def visitElement_spec(self, ctx:PlSqlParser.Element_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#element_spec_options.
    def visitElement_spec_options(self, ctx:PlSqlParser.Element_spec_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subprogram_spec.
    def visitSubprogram_spec(self, ctx:PlSqlParser.Subprogram_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#overriding_subprogram_spec.
    def visitOverriding_subprogram_spec(self, ctx:PlSqlParser.Overriding_subprogram_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#overriding_function_spec.
    def visitOverriding_function_spec(self, ctx:PlSqlParser.Overriding_function_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#overriding_procedure_spec.
    def visitOverriding_procedure_spec(self, ctx:PlSqlParser.Overriding_procedure_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_procedure_spec.
    def visitType_procedure_spec(self, ctx:PlSqlParser.Type_procedure_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_function_spec.
    def visitType_function_spec(self, ctx:PlSqlParser.Type_function_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#constructor_spec.
    def visitConstructor_spec(self, ctx:PlSqlParser.Constructor_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#map_order_function_spec.
    def visitMap_order_function_spec(self, ctx:PlSqlParser.Map_order_function_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pragma_clause.
    def visitPragma_clause(self, ctx:PlSqlParser.Pragma_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pragma_elements.
    def visitPragma_elements(self, ctx:PlSqlParser.Pragma_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_elements_parameter.
    def visitType_elements_parameter(self, ctx:PlSqlParser.Type_elements_parameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_sequence.
    def visitDrop_sequence(self, ctx:PlSqlParser.Drop_sequenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_sequence.
    def visitAlter_sequence(self, ctx:PlSqlParser.Alter_sequenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_session.
    def visitAlter_session(self, ctx:PlSqlParser.Alter_sessionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_session_set_clause.
    def visitAlter_session_set_clause(self, ctx:PlSqlParser.Alter_session_set_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_sequence.
    def visitCreate_sequence(self, ctx:PlSqlParser.Create_sequenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sequence_spec.
    def visitSequence_spec(self, ctx:PlSqlParser.Sequence_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sequence_start_clause.
    def visitSequence_start_clause(self, ctx:PlSqlParser.Sequence_start_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_analytic_view.
    def visitCreate_analytic_view(self, ctx:PlSqlParser.Create_analytic_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#classification_clause.
    def visitClassification_clause(self, ctx:PlSqlParser.Classification_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#caption_clause.
    def visitCaption_clause(self, ctx:PlSqlParser.Caption_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#description_clause.
    def visitDescription_clause(self, ctx:PlSqlParser.Description_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#classification_item.
    def visitClassification_item(self, ctx:PlSqlParser.Classification_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#language.
    def visitLanguage(self, ctx:PlSqlParser.LanguageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cav_using_clause.
    def visitCav_using_clause(self, ctx:PlSqlParser.Cav_using_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dim_by_clause.
    def visitDim_by_clause(self, ctx:PlSqlParser.Dim_by_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dim_key.
    def visitDim_key(self, ctx:PlSqlParser.Dim_keyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dim_ref.
    def visitDim_ref(self, ctx:PlSqlParser.Dim_refContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hier_ref.
    def visitHier_ref(self, ctx:PlSqlParser.Hier_refContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#measures_clause.
    def visitMeasures_clause(self, ctx:PlSqlParser.Measures_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#av_measure.
    def visitAv_measure(self, ctx:PlSqlParser.Av_measureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#base_meas_clause.
    def visitBase_meas_clause(self, ctx:PlSqlParser.Base_meas_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#meas_aggregate_clause.
    def visitMeas_aggregate_clause(self, ctx:PlSqlParser.Meas_aggregate_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#calc_meas_clause.
    def visitCalc_meas_clause(self, ctx:PlSqlParser.Calc_meas_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_measure_clause.
    def visitDefault_measure_clause(self, ctx:PlSqlParser.Default_measure_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_aggregate_clause.
    def visitDefault_aggregate_clause(self, ctx:PlSqlParser.Default_aggregate_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cache_clause.
    def visitCache_clause(self, ctx:PlSqlParser.Cache_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cache_specification.
    def visitCache_specification(self, ctx:PlSqlParser.Cache_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#levels_clause.
    def visitLevels_clause(self, ctx:PlSqlParser.Levels_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#level_specification.
    def visitLevel_specification(self, ctx:PlSqlParser.Level_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#level_group_type.
    def visitLevel_group_type(self, ctx:PlSqlParser.Level_group_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#fact_columns_clause.
    def visitFact_columns_clause(self, ctx:PlSqlParser.Fact_columns_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#qry_transform_clause.
    def visitQry_transform_clause(self, ctx:PlSqlParser.Qry_transform_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_attribute_dimension.
    def visitCreate_attribute_dimension(self, ctx:PlSqlParser.Create_attribute_dimensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ad_using_clause.
    def visitAd_using_clause(self, ctx:PlSqlParser.Ad_using_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#source_clause.
    def visitSource_clause(self, ctx:PlSqlParser.Source_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#join_path_clause.
    def visitJoin_path_clause(self, ctx:PlSqlParser.Join_path_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#join_condition.
    def visitJoin_condition(self, ctx:PlSqlParser.Join_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#join_condition_item.
    def visitJoin_condition_item(self, ctx:PlSqlParser.Join_condition_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#attributes_clause.
    def visitAttributes_clause(self, ctx:PlSqlParser.Attributes_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ad_attributes_clause.
    def visitAd_attributes_clause(self, ctx:PlSqlParser.Ad_attributes_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ad_level_clause.
    def visitAd_level_clause(self, ctx:PlSqlParser.Ad_level_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#key_clause.
    def visitKey_clause(self, ctx:PlSqlParser.Key_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alternate_key_clause.
    def visitAlternate_key_clause(self, ctx:PlSqlParser.Alternate_key_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dim_order_clause.
    def visitDim_order_clause(self, ctx:PlSqlParser.Dim_order_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#all_clause.
    def visitAll_clause(self, ctx:PlSqlParser.All_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_audit_policy.
    def visitCreate_audit_policy(self, ctx:PlSqlParser.Create_audit_policyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#privilege_audit_clause.
    def visitPrivilege_audit_clause(self, ctx:PlSqlParser.Privilege_audit_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#action_audit_clause.
    def visitAction_audit_clause(self, ctx:PlSqlParser.Action_audit_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#system_actions.
    def visitSystem_actions(self, ctx:PlSqlParser.System_actionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#standard_actions.
    def visitStandard_actions(self, ctx:PlSqlParser.Standard_actionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#actions_clause.
    def visitActions_clause(self, ctx:PlSqlParser.Actions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_action.
    def visitObject_action(self, ctx:PlSqlParser.Object_actionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#system_action.
    def visitSystem_action(self, ctx:PlSqlParser.System_actionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#component_actions.
    def visitComponent_actions(self, ctx:PlSqlParser.Component_actionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#component_action.
    def visitComponent_action(self, ctx:PlSqlParser.Component_actionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#role_audit_clause.
    def visitRole_audit_clause(self, ctx:PlSqlParser.Role_audit_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_controlfile.
    def visitCreate_controlfile(self, ctx:PlSqlParser.Create_controlfileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#controlfile_options.
    def visitControlfile_options(self, ctx:PlSqlParser.Controlfile_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#logfile_clause.
    def visitLogfile_clause(self, ctx:PlSqlParser.Logfile_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#character_set_clause.
    def visitCharacter_set_clause(self, ctx:PlSqlParser.Character_set_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#file_specification.
    def visitFile_specification(self, ctx:PlSqlParser.File_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_diskgroup.
    def visitCreate_diskgroup(self, ctx:PlSqlParser.Create_diskgroupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#qualified_disk_clause.
    def visitQualified_disk_clause(self, ctx:PlSqlParser.Qualified_disk_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_edition.
    def visitCreate_edition(self, ctx:PlSqlParser.Create_editionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_flashback_archive.
    def visitCreate_flashback_archive(self, ctx:PlSqlParser.Create_flashback_archiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#flashback_archive_quota.
    def visitFlashback_archive_quota(self, ctx:PlSqlParser.Flashback_archive_quotaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#flashback_archive_retention.
    def visitFlashback_archive_retention(self, ctx:PlSqlParser.Flashback_archive_retentionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_hierarchy.
    def visitCreate_hierarchy(self, ctx:PlSqlParser.Create_hierarchyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hier_using_clause.
    def visitHier_using_clause(self, ctx:PlSqlParser.Hier_using_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#level_hier_clause.
    def visitLevel_hier_clause(self, ctx:PlSqlParser.Level_hier_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hier_attrs_clause.
    def visitHier_attrs_clause(self, ctx:PlSqlParser.Hier_attrs_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hier_attr_clause.
    def visitHier_attr_clause(self, ctx:PlSqlParser.Hier_attr_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hier_attr_name.
    def visitHier_attr_name(self, ctx:PlSqlParser.Hier_attr_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_index.
    def visitCreate_index(self, ctx:PlSqlParser.Create_indexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cluster_index_clause.
    def visitCluster_index_clause(self, ctx:PlSqlParser.Cluster_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cluster_name.
    def visitCluster_name(self, ctx:PlSqlParser.Cluster_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_index_clause.
    def visitTable_index_clause(self, ctx:PlSqlParser.Table_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#bitmap_join_index_clause.
    def visitBitmap_join_index_clause(self, ctx:PlSqlParser.Bitmap_join_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_expr.
    def visitIndex_expr(self, ctx:PlSqlParser.Index_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_properties.
    def visitIndex_properties(self, ctx:PlSqlParser.Index_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#domain_index_clause.
    def visitDomain_index_clause(self, ctx:PlSqlParser.Domain_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#local_domain_index_clause.
    def visitLocal_domain_index_clause(self, ctx:PlSqlParser.Local_domain_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmlindex_clause.
    def visitXmlindex_clause(self, ctx:PlSqlParser.Xmlindex_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#local_xmlindex_clause.
    def visitLocal_xmlindex_clause(self, ctx:PlSqlParser.Local_xmlindex_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#global_partitioned_index.
    def visitGlobal_partitioned_index(self, ctx:PlSqlParser.Global_partitioned_indexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_partitioning_clause.
    def visitIndex_partitioning_clause(self, ctx:PlSqlParser.Index_partitioning_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_partitioning_values_list.
    def visitIndex_partitioning_values_list(self, ctx:PlSqlParser.Index_partitioning_values_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#local_partitioned_index.
    def visitLocal_partitioned_index(self, ctx:PlSqlParser.Local_partitioned_indexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#on_range_partitioned_table.
    def visitOn_range_partitioned_table(self, ctx:PlSqlParser.On_range_partitioned_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#on_list_partitioned_table.
    def visitOn_list_partitioned_table(self, ctx:PlSqlParser.On_list_partitioned_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partitioned_table.
    def visitPartitioned_table(self, ctx:PlSqlParser.Partitioned_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#on_hash_partitioned_table.
    def visitOn_hash_partitioned_table(self, ctx:PlSqlParser.On_hash_partitioned_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#on_hash_partitioned_clause.
    def visitOn_hash_partitioned_clause(self, ctx:PlSqlParser.On_hash_partitioned_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#on_comp_partitioned_table.
    def visitOn_comp_partitioned_table(self, ctx:PlSqlParser.On_comp_partitioned_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#on_comp_partitioned_clause.
    def visitOn_comp_partitioned_clause(self, ctx:PlSqlParser.On_comp_partitioned_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_subpartition_clause.
    def visitIndex_subpartition_clause(self, ctx:PlSqlParser.Index_subpartition_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_subpartition_subclause.
    def visitIndex_subpartition_subclause(self, ctx:PlSqlParser.Index_subpartition_subclauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#odci_parameters.
    def visitOdci_parameters(self, ctx:PlSqlParser.Odci_parametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#indextype.
    def visitIndextype(self, ctx:PlSqlParser.IndextypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_index.
    def visitAlter_index(self, ctx:PlSqlParser.Alter_indexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_index_ops_set1.
    def visitAlter_index_ops_set1(self, ctx:PlSqlParser.Alter_index_ops_set1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_index_ops_set2.
    def visitAlter_index_ops_set2(self, ctx:PlSqlParser.Alter_index_ops_set2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#visible_or_invisible.
    def visitVisible_or_invisible(self, ctx:PlSqlParser.Visible_or_invisibleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#monitoring_nomonitoring.
    def visitMonitoring_nomonitoring(self, ctx:PlSqlParser.Monitoring_nomonitoringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rebuild_clause.
    def visitRebuild_clause(self, ctx:PlSqlParser.Rebuild_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_index_partitioning.
    def visitAlter_index_partitioning(self, ctx:PlSqlParser.Alter_index_partitioningContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_index_default_attrs.
    def visitModify_index_default_attrs(self, ctx:PlSqlParser.Modify_index_default_attrsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_hash_index_partition.
    def visitAdd_hash_index_partition(self, ctx:PlSqlParser.Add_hash_index_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#coalesce_index_partition.
    def visitCoalesce_index_partition(self, ctx:PlSqlParser.Coalesce_index_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_index_partition.
    def visitModify_index_partition(self, ctx:PlSqlParser.Modify_index_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_index_partitions_ops.
    def visitModify_index_partitions_ops(self, ctx:PlSqlParser.Modify_index_partitions_opsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rename_index_partition.
    def visitRename_index_partition(self, ctx:PlSqlParser.Rename_index_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_index_partition.
    def visitDrop_index_partition(self, ctx:PlSqlParser.Drop_index_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#split_index_partition.
    def visitSplit_index_partition(self, ctx:PlSqlParser.Split_index_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_partition_description.
    def visitIndex_partition_description(self, ctx:PlSqlParser.Index_partition_descriptionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_index_subpartition.
    def visitModify_index_subpartition(self, ctx:PlSqlParser.Modify_index_subpartitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partition_name_old.
    def visitPartition_name_old(self, ctx:PlSqlParser.Partition_name_oldContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#new_partition_name.
    def visitNew_partition_name(self, ctx:PlSqlParser.New_partition_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#new_index_name.
    def visitNew_index_name(self, ctx:PlSqlParser.New_index_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_inmemory_join_group.
    def visitAlter_inmemory_join_group(self, ctx:PlSqlParser.Alter_inmemory_join_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_user.
    def visitCreate_user(self, ctx:PlSqlParser.Create_userContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_user.
    def visitAlter_user(self, ctx:PlSqlParser.Alter_userContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_user.
    def visitDrop_user(self, ctx:PlSqlParser.Drop_userContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_identified_by.
    def visitAlter_identified_by(self, ctx:PlSqlParser.Alter_identified_byContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#identified_by.
    def visitIdentified_by(self, ctx:PlSqlParser.Identified_byContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#identified_other_clause.
    def visitIdentified_other_clause(self, ctx:PlSqlParser.Identified_other_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#user_tablespace_clause.
    def visitUser_tablespace_clause(self, ctx:PlSqlParser.User_tablespace_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#quota_clause.
    def visitQuota_clause(self, ctx:PlSqlParser.Quota_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#profile_clause.
    def visitProfile_clause(self, ctx:PlSqlParser.Profile_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#role_clause.
    def visitRole_clause(self, ctx:PlSqlParser.Role_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#user_default_role_clause.
    def visitUser_default_role_clause(self, ctx:PlSqlParser.User_default_role_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#password_expire_clause.
    def visitPassword_expire_clause(self, ctx:PlSqlParser.Password_expire_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#user_lock_clause.
    def visitUser_lock_clause(self, ctx:PlSqlParser.User_lock_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#user_editions_clause.
    def visitUser_editions_clause(self, ctx:PlSqlParser.User_editions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_user_editions_clause.
    def visitAlter_user_editions_clause(self, ctx:PlSqlParser.Alter_user_editions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#proxy_clause.
    def visitProxy_clause(self, ctx:PlSqlParser.Proxy_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#container_names.
    def visitContainer_names(self, ctx:PlSqlParser.Container_namesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#set_container_data.
    def visitSet_container_data(self, ctx:PlSqlParser.Set_container_dataContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_rem_container_data.
    def visitAdd_rem_container_data(self, ctx:PlSqlParser.Add_rem_container_dataContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#container_data_clause.
    def visitContainer_data_clause(self, ctx:PlSqlParser.Container_data_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#administer_key_management.
    def visitAdminister_key_management(self, ctx:PlSqlParser.Administer_key_managementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#keystore_management_clauses.
    def visitKeystore_management_clauses(self, ctx:PlSqlParser.Keystore_management_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_keystore.
    def visitCreate_keystore(self, ctx:PlSqlParser.Create_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#open_keystore.
    def visitOpen_keystore(self, ctx:PlSqlParser.Open_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#force_keystore.
    def visitForce_keystore(self, ctx:PlSqlParser.Force_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#close_keystore.
    def visitClose_keystore(self, ctx:PlSqlParser.Close_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#backup_keystore.
    def visitBackup_keystore(self, ctx:PlSqlParser.Backup_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_keystore_password.
    def visitAlter_keystore_password(self, ctx:PlSqlParser.Alter_keystore_passwordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#merge_into_new_keystore.
    def visitMerge_into_new_keystore(self, ctx:PlSqlParser.Merge_into_new_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#merge_into_existing_keystore.
    def visitMerge_into_existing_keystore(self, ctx:PlSqlParser.Merge_into_existing_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#isolate_keystore.
    def visitIsolate_keystore(self, ctx:PlSqlParser.Isolate_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unite_keystore.
    def visitUnite_keystore(self, ctx:PlSqlParser.Unite_keystoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#key_management_clauses.
    def visitKey_management_clauses(self, ctx:PlSqlParser.Key_management_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#set_key.
    def visitSet_key(self, ctx:PlSqlParser.Set_keyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_key.
    def visitCreate_key(self, ctx:PlSqlParser.Create_keyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#mkid.
    def visitMkid(self, ctx:PlSqlParser.MkidContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#mk.
    def visitMk(self, ctx:PlSqlParser.MkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#use_key.
    def visitUse_key(self, ctx:PlSqlParser.Use_keyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#set_key_tag.
    def visitSet_key_tag(self, ctx:PlSqlParser.Set_key_tagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#export_keys.
    def visitExport_keys(self, ctx:PlSqlParser.Export_keysContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#import_keys.
    def visitImport_keys(self, ctx:PlSqlParser.Import_keysContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#migrate_keys.
    def visitMigrate_keys(self, ctx:PlSqlParser.Migrate_keysContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#reverse_migrate_keys.
    def visitReverse_migrate_keys(self, ctx:PlSqlParser.Reverse_migrate_keysContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#move_keys.
    def visitMove_keys(self, ctx:PlSqlParser.Move_keysContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#identified_by_store.
    def visitIdentified_by_store(self, ctx:PlSqlParser.Identified_by_storeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#using_algorithm_clause.
    def visitUsing_algorithm_clause(self, ctx:PlSqlParser.Using_algorithm_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#using_tag_clause.
    def visitUsing_tag_clause(self, ctx:PlSqlParser.Using_tag_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#secret_management_clauses.
    def visitSecret_management_clauses(self, ctx:PlSqlParser.Secret_management_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_update_secret.
    def visitAdd_update_secret(self, ctx:PlSqlParser.Add_update_secretContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#delete_secret.
    def visitDelete_secret(self, ctx:PlSqlParser.Delete_secretContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_update_secret_seps.
    def visitAdd_update_secret_seps(self, ctx:PlSqlParser.Add_update_secret_sepsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#delete_secret_seps.
    def visitDelete_secret_seps(self, ctx:PlSqlParser.Delete_secret_sepsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#zero_downtime_software_patching_clauses.
    def visitZero_downtime_software_patching_clauses(self, ctx:PlSqlParser.Zero_downtime_software_patching_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#with_backup_clause.
    def visitWith_backup_clause(self, ctx:PlSqlParser.With_backup_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#identified_by_password_clause.
    def visitIdentified_by_password_clause(self, ctx:PlSqlParser.Identified_by_password_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#keystore_password.
    def visitKeystore_password(self, ctx:PlSqlParser.Keystore_passwordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#path.
    def visitPath(self, ctx:PlSqlParser.PathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#secret.
    def visitSecret(self, ctx:PlSqlParser.SecretContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#analyze.
    def visitAnalyze(self, ctx:PlSqlParser.AnalyzeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partition_extention_clause.
    def visitPartition_extention_clause(self, ctx:PlSqlParser.Partition_extention_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#validation_clauses.
    def visitValidation_clauses(self, ctx:PlSqlParser.Validation_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#compute_clauses.
    def visitCompute_clauses(self, ctx:PlSqlParser.Compute_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#for_clause.
    def visitFor_clause(self, ctx:PlSqlParser.For_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#online_or_offline.
    def visitOnline_or_offline(self, ctx:PlSqlParser.Online_or_offlineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#into_clause1.
    def visitInto_clause1(self, ctx:PlSqlParser.Into_clause1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partition_key_value.
    def visitPartition_key_value(self, ctx:PlSqlParser.Partition_key_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subpartition_key_value.
    def visitSubpartition_key_value(self, ctx:PlSqlParser.Subpartition_key_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#associate_statistics.
    def visitAssociate_statistics(self, ctx:PlSqlParser.Associate_statisticsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_association.
    def visitColumn_association(self, ctx:PlSqlParser.Column_associationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#function_association.
    def visitFunction_association(self, ctx:PlSqlParser.Function_associationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#indextype_name.
    def visitIndextype_name(self, ctx:PlSqlParser.Indextype_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#using_statistics_type.
    def visitUsing_statistics_type(self, ctx:PlSqlParser.Using_statistics_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#statistics_type_name.
    def visitStatistics_type_name(self, ctx:PlSqlParser.Statistics_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_cost_clause.
    def visitDefault_cost_clause(self, ctx:PlSqlParser.Default_cost_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cpu_cost.
    def visitCpu_cost(self, ctx:PlSqlParser.Cpu_costContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#io_cost.
    def visitIo_cost(self, ctx:PlSqlParser.Io_costContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#network_cost.
    def visitNetwork_cost(self, ctx:PlSqlParser.Network_costContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_selectivity_clause.
    def visitDefault_selectivity_clause(self, ctx:PlSqlParser.Default_selectivity_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_selectivity.
    def visitDefault_selectivity(self, ctx:PlSqlParser.Default_selectivityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#storage_table_clause.
    def visitStorage_table_clause(self, ctx:PlSqlParser.Storage_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unified_auditing.
    def visitUnified_auditing(self, ctx:PlSqlParser.Unified_auditingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#policy_name.
    def visitPolicy_name(self, ctx:PlSqlParser.Policy_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#audit_traditional.
    def visitAudit_traditional(self, ctx:PlSqlParser.Audit_traditionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#audit_direct_path.
    def visitAudit_direct_path(self, ctx:PlSqlParser.Audit_direct_pathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#audit_container_clause.
    def visitAudit_container_clause(self, ctx:PlSqlParser.Audit_container_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#audit_operation_clause.
    def visitAudit_operation_clause(self, ctx:PlSqlParser.Audit_operation_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#auditing_by_clause.
    def visitAuditing_by_clause(self, ctx:PlSqlParser.Auditing_by_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#audit_user.
    def visitAudit_user(self, ctx:PlSqlParser.Audit_userContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#audit_schema_object_clause.
    def visitAudit_schema_object_clause(self, ctx:PlSqlParser.Audit_schema_object_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sql_operation.
    def visitSql_operation(self, ctx:PlSqlParser.Sql_operationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#auditing_on_clause.
    def visitAuditing_on_clause(self, ctx:PlSqlParser.Auditing_on_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_name.
    def visitModel_name(self, ctx:PlSqlParser.Model_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_name.
    def visitObject_name(self, ctx:PlSqlParser.Object_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#profile_name.
    def visitProfile_name(self, ctx:PlSqlParser.Profile_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sql_statement_shortcut.
    def visitSql_statement_shortcut(self, ctx:PlSqlParser.Sql_statement_shortcutContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_index.
    def visitDrop_index(self, ctx:PlSqlParser.Drop_indexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#disassociate_statistics.
    def visitDisassociate_statistics(self, ctx:PlSqlParser.Disassociate_statisticsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_indextype.
    def visitDrop_indextype(self, ctx:PlSqlParser.Drop_indextypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_inmemory_join_group.
    def visitDrop_inmemory_join_group(self, ctx:PlSqlParser.Drop_inmemory_join_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#flashback_table.
    def visitFlashback_table(self, ctx:PlSqlParser.Flashback_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#restore_point.
    def visitRestore_point(self, ctx:PlSqlParser.Restore_pointContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#purge_statement.
    def visitPurge_statement(self, ctx:PlSqlParser.Purge_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#noaudit_statement.
    def visitNoaudit_statement(self, ctx:PlSqlParser.Noaudit_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rename_object.
    def visitRename_object(self, ctx:PlSqlParser.Rename_objectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#grant_statement.
    def visitGrant_statement(self, ctx:PlSqlParser.Grant_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#container_clause.
    def visitContainer_clause(self, ctx:PlSqlParser.Container_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#revoke_statement.
    def visitRevoke_statement(self, ctx:PlSqlParser.Revoke_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#revoke_system_privilege.
    def visitRevoke_system_privilege(self, ctx:PlSqlParser.Revoke_system_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#revokee_clause.
    def visitRevokee_clause(self, ctx:PlSqlParser.Revokee_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#revoke_object_privileges.
    def visitRevoke_object_privileges(self, ctx:PlSqlParser.Revoke_object_privilegesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#on_object_clause.
    def visitOn_object_clause(self, ctx:PlSqlParser.On_object_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#revoke_roles_from_programs.
    def visitRevoke_roles_from_programs(self, ctx:PlSqlParser.Revoke_roles_from_programsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#program_unit.
    def visitProgram_unit(self, ctx:PlSqlParser.Program_unitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_dimension.
    def visitCreate_dimension(self, ctx:PlSqlParser.Create_dimensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_directory.
    def visitCreate_directory(self, ctx:PlSqlParser.Create_directoryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#directory_name.
    def visitDirectory_name(self, ctx:PlSqlParser.Directory_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#directory_path.
    def visitDirectory_path(self, ctx:PlSqlParser.Directory_pathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_inmemory_join_group.
    def visitCreate_inmemory_join_group(self, ctx:PlSqlParser.Create_inmemory_join_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_hierarchy.
    def visitDrop_hierarchy(self, ctx:PlSqlParser.Drop_hierarchyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_library.
    def visitAlter_library(self, ctx:PlSqlParser.Alter_libraryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_java.
    def visitDrop_java(self, ctx:PlSqlParser.Drop_javaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_library.
    def visitDrop_library(self, ctx:PlSqlParser.Drop_libraryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_java.
    def visitCreate_java(self, ctx:PlSqlParser.Create_javaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_library.
    def visitCreate_library(self, ctx:PlSqlParser.Create_libraryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#plsql_library_source.
    def visitPlsql_library_source(self, ctx:PlSqlParser.Plsql_library_sourceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#credential_name.
    def visitCredential_name(self, ctx:PlSqlParser.Credential_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#library_editionable.
    def visitLibrary_editionable(self, ctx:PlSqlParser.Library_editionableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#library_debug.
    def visitLibrary_debug(self, ctx:PlSqlParser.Library_debugContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#compiler_parameters_clause.
    def visitCompiler_parameters_clause(self, ctx:PlSqlParser.Compiler_parameters_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#parameter_value.
    def visitParameter_value(self, ctx:PlSqlParser.Parameter_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#library_name.
    def visitLibrary_name(self, ctx:PlSqlParser.Library_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_dimension.
    def visitAlter_dimension(self, ctx:PlSqlParser.Alter_dimensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#level_clause.
    def visitLevel_clause(self, ctx:PlSqlParser.Level_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hierarchy_clause.
    def visitHierarchy_clause(self, ctx:PlSqlParser.Hierarchy_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dimension_join_clause.
    def visitDimension_join_clause(self, ctx:PlSqlParser.Dimension_join_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#attribute_clause.
    def visitAttribute_clause(self, ctx:PlSqlParser.Attribute_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#extended_attribute_clause.
    def visitExtended_attribute_clause(self, ctx:PlSqlParser.Extended_attribute_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_one_or_more_sub_clause.
    def visitColumn_one_or_more_sub_clause(self, ctx:PlSqlParser.Column_one_or_more_sub_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_view.
    def visitAlter_view(self, ctx:PlSqlParser.Alter_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_view_editionable.
    def visitAlter_view_editionable(self, ctx:PlSqlParser.Alter_view_editionableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_view.
    def visitCreate_view(self, ctx:PlSqlParser.Create_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#editioning_clause.
    def visitEditioning_clause(self, ctx:PlSqlParser.Editioning_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#view_options.
    def visitView_options(self, ctx:PlSqlParser.View_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#view_alias_constraint.
    def visitView_alias_constraint(self, ctx:PlSqlParser.View_alias_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_view_clause.
    def visitObject_view_clause(self, ctx:PlSqlParser.Object_view_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inline_constraint.
    def visitInline_constraint(self, ctx:PlSqlParser.Inline_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inline_ref_constraint.
    def visitInline_ref_constraint(self, ctx:PlSqlParser.Inline_ref_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#out_of_line_ref_constraint.
    def visitOut_of_line_ref_constraint(self, ctx:PlSqlParser.Out_of_line_ref_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#out_of_line_constraint.
    def visitOut_of_line_constraint(self, ctx:PlSqlParser.Out_of_line_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#constraint_state.
    def visitConstraint_state(self, ctx:PlSqlParser.Constraint_stateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmltype_view_clause.
    def visitXmltype_view_clause(self, ctx:PlSqlParser.Xmltype_view_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_schema_spec.
    def visitXml_schema_spec(self, ctx:PlSqlParser.Xml_schema_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_schema_url.
    def visitXml_schema_url(self, ctx:PlSqlParser.Xml_schema_urlContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#element.
    def visitElement(self, ctx:PlSqlParser.ElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_tablespace.
    def visitAlter_tablespace(self, ctx:PlSqlParser.Alter_tablespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#datafile_tempfile_clauses.
    def visitDatafile_tempfile_clauses(self, ctx:PlSqlParser.Datafile_tempfile_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_logging_clauses.
    def visitTablespace_logging_clauses(self, ctx:PlSqlParser.Tablespace_logging_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_group_clause.
    def visitTablespace_group_clause(self, ctx:PlSqlParser.Tablespace_group_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_group_name.
    def visitTablespace_group_name(self, ctx:PlSqlParser.Tablespace_group_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_state_clauses.
    def visitTablespace_state_clauses(self, ctx:PlSqlParser.Tablespace_state_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#flashback_mode_clause.
    def visitFlashback_mode_clause(self, ctx:PlSqlParser.Flashback_mode_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#new_tablespace_name.
    def visitNew_tablespace_name(self, ctx:PlSqlParser.New_tablespace_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_tablespace.
    def visitCreate_tablespace(self, ctx:PlSqlParser.Create_tablespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#permanent_tablespace_clause.
    def visitPermanent_tablespace_clause(self, ctx:PlSqlParser.Permanent_tablespace_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_encryption_spec.
    def visitTablespace_encryption_spec(self, ctx:PlSqlParser.Tablespace_encryption_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#logging_clause.
    def visitLogging_clause(self, ctx:PlSqlParser.Logging_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#extent_management_clause.
    def visitExtent_management_clause(self, ctx:PlSqlParser.Extent_management_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#segment_management_clause.
    def visitSegment_management_clause(self, ctx:PlSqlParser.Segment_management_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#temporary_tablespace_clause.
    def visitTemporary_tablespace_clause(self, ctx:PlSqlParser.Temporary_tablespace_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#undo_tablespace_clause.
    def visitUndo_tablespace_clause(self, ctx:PlSqlParser.Undo_tablespace_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_retention_clause.
    def visitTablespace_retention_clause(self, ctx:PlSqlParser.Tablespace_retention_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_tablespace_set.
    def visitCreate_tablespace_set(self, ctx:PlSqlParser.Create_tablespace_setContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#permanent_tablespace_attrs.
    def visitPermanent_tablespace_attrs(self, ctx:PlSqlParser.Permanent_tablespace_attrsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_encryption_clause.
    def visitTablespace_encryption_clause(self, ctx:PlSqlParser.Tablespace_encryption_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_tablespace_params.
    def visitDefault_tablespace_params(self, ctx:PlSqlParser.Default_tablespace_paramsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_table_compression.
    def visitDefault_table_compression(self, ctx:PlSqlParser.Default_table_compressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#low_high.
    def visitLow_high(self, ctx:PlSqlParser.Low_highContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_index_compression.
    def visitDefault_index_compression(self, ctx:PlSqlParser.Default_index_compressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inmmemory_clause.
    def visitInmmemory_clause(self, ctx:PlSqlParser.Inmmemory_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#datafile_specification.
    def visitDatafile_specification(self, ctx:PlSqlParser.Datafile_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tempfile_specification.
    def visitTempfile_specification(self, ctx:PlSqlParser.Tempfile_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#datafile_tempfile_spec.
    def visitDatafile_tempfile_spec(self, ctx:PlSqlParser.Datafile_tempfile_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#redo_log_file_spec.
    def visitRedo_log_file_spec(self, ctx:PlSqlParser.Redo_log_file_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#autoextend_clause.
    def visitAutoextend_clause(self, ctx:PlSqlParser.Autoextend_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#maxsize_clause.
    def visitMaxsize_clause(self, ctx:PlSqlParser.Maxsize_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#build_clause.
    def visitBuild_clause(self, ctx:PlSqlParser.Build_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#parallel_clause.
    def visitParallel_clause(self, ctx:PlSqlParser.Parallel_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#parallel_instances_clause.
    def visitParallel_instances_clause(self, ctx:PlSqlParser.Parallel_instances_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_materialized_view.
    def visitAlter_materialized_view(self, ctx:PlSqlParser.Alter_materialized_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_mv_option1.
    def visitAlter_mv_option1(self, ctx:PlSqlParser.Alter_mv_option1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_mv_refresh.
    def visitAlter_mv_refresh(self, ctx:PlSqlParser.Alter_mv_refreshContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rollback_segment.
    def visitRollback_segment(self, ctx:PlSqlParser.Rollback_segmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_mv_column_clause.
    def visitModify_mv_column_clause(self, ctx:PlSqlParser.Modify_mv_column_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_materialized_view_log.
    def visitAlter_materialized_view_log(self, ctx:PlSqlParser.Alter_materialized_view_logContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_mv_log_column_clause.
    def visitAdd_mv_log_column_clause(self, ctx:PlSqlParser.Add_mv_log_column_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#move_mv_log_clause.
    def visitMove_mv_log_clause(self, ctx:PlSqlParser.Move_mv_log_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#mv_log_augmentation.
    def visitMv_log_augmentation(self, ctx:PlSqlParser.Mv_log_augmentationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_materialized_view_log.
    def visitCreate_materialized_view_log(self, ctx:PlSqlParser.Create_materialized_view_logContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#new_values_clause.
    def visitNew_values_clause(self, ctx:PlSqlParser.New_values_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#mv_log_purge_clause.
    def visitMv_log_purge_clause(self, ctx:PlSqlParser.Mv_log_purge_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_materialized_zonemap.
    def visitCreate_materialized_zonemap(self, ctx:PlSqlParser.Create_materialized_zonemapContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_materialized_zonemap.
    def visitAlter_materialized_zonemap(self, ctx:PlSqlParser.Alter_materialized_zonemapContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_materialized_zonemap.
    def visitDrop_materialized_zonemap(self, ctx:PlSqlParser.Drop_materialized_zonemapContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#zonemap_refresh_clause.
    def visitZonemap_refresh_clause(self, ctx:PlSqlParser.Zonemap_refresh_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#zonemap_attributes.
    def visitZonemap_attributes(self, ctx:PlSqlParser.Zonemap_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#zonemap_name.
    def visitZonemap_name(self, ctx:PlSqlParser.Zonemap_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#operator_name.
    def visitOperator_name(self, ctx:PlSqlParser.Operator_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#operator_function_name.
    def visitOperator_function_name(self, ctx:PlSqlParser.Operator_function_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_zonemap_on_table.
    def visitCreate_zonemap_on_table(self, ctx:PlSqlParser.Create_zonemap_on_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_zonemap_as_subquery.
    def visitCreate_zonemap_as_subquery(self, ctx:PlSqlParser.Create_zonemap_as_subqueryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_operator.
    def visitAlter_operator(self, ctx:PlSqlParser.Alter_operatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_operator.
    def visitDrop_operator(self, ctx:PlSqlParser.Drop_operatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_operator.
    def visitCreate_operator(self, ctx:PlSqlParser.Create_operatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#binding_clause.
    def visitBinding_clause(self, ctx:PlSqlParser.Binding_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_binding_clause.
    def visitAdd_binding_clause(self, ctx:PlSqlParser.Add_binding_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#implementation_clause.
    def visitImplementation_clause(self, ctx:PlSqlParser.Implementation_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#primary_operator_list.
    def visitPrimary_operator_list(self, ctx:PlSqlParser.Primary_operator_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#primary_operator_item.
    def visitPrimary_operator_item(self, ctx:PlSqlParser.Primary_operator_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#operator_context_clause.
    def visitOperator_context_clause(self, ctx:PlSqlParser.Operator_context_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#using_function_clause.
    def visitUsing_function_clause(self, ctx:PlSqlParser.Using_function_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_binding_clause.
    def visitDrop_binding_clause(self, ctx:PlSqlParser.Drop_binding_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_materialized_view.
    def visitCreate_materialized_view(self, ctx:PlSqlParser.Create_materialized_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#scoped_table_ref_constraint.
    def visitScoped_table_ref_constraint(self, ctx:PlSqlParser.Scoped_table_ref_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#mv_column_alias.
    def visitMv_column_alias(self, ctx:PlSqlParser.Mv_column_aliasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_mv_refresh.
    def visitCreate_mv_refresh(self, ctx:PlSqlParser.Create_mv_refreshContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#query_rewrite_clause.
    def visitQuery_rewrite_clause(self, ctx:PlSqlParser.Query_rewrite_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unusable_editions_clause.
    def visitUnusable_editions_clause(self, ctx:PlSqlParser.Unusable_editions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_materialized_view.
    def visitDrop_materialized_view(self, ctx:PlSqlParser.Drop_materialized_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_materialized_view_log.
    def visitDrop_materialized_view_log(self, ctx:PlSqlParser.Drop_materialized_view_logContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_context.
    def visitCreate_context(self, ctx:PlSqlParser.Create_contextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#oracle_namespace.
    def visitOracle_namespace(self, ctx:PlSqlParser.Oracle_namespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_cluster.
    def visitCreate_cluster(self, ctx:PlSqlParser.Create_clusterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_profile.
    def visitCreate_profile(self, ctx:PlSqlParser.Create_profileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#resource_parameters.
    def visitResource_parameters(self, ctx:PlSqlParser.Resource_parametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#password_parameters.
    def visitPassword_parameters(self, ctx:PlSqlParser.Password_parametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_lockdown_profile.
    def visitCreate_lockdown_profile(self, ctx:PlSqlParser.Create_lockdown_profileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#static_base_profile.
    def visitStatic_base_profile(self, ctx:PlSqlParser.Static_base_profileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dynamic_base_profile.
    def visitDynamic_base_profile(self, ctx:PlSqlParser.Dynamic_base_profileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_outline.
    def visitCreate_outline(self, ctx:PlSqlParser.Create_outlineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_restore_point.
    def visitCreate_restore_point(self, ctx:PlSqlParser.Create_restore_pointContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_role.
    def visitCreate_role(self, ctx:PlSqlParser.Create_roleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_table.
    def visitCreate_table(self, ctx:PlSqlParser.Create_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmltype_table.
    def visitXmltype_table(self, ctx:PlSqlParser.Xmltype_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmltype_virtual_columns.
    def visitXmltype_virtual_columns(self, ctx:PlSqlParser.Xmltype_virtual_columnsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmltype_column_properties.
    def visitXmltype_column_properties(self, ctx:PlSqlParser.Xmltype_column_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmltype_storage.
    def visitXmltype_storage(self, ctx:PlSqlParser.Xmltype_storageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmlschema_spec.
    def visitXmlschema_spec(self, ctx:PlSqlParser.Xmlschema_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_table.
    def visitObject_table(self, ctx:PlSqlParser.Object_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_type.
    def visitObject_type(self, ctx:PlSqlParser.Object_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#oid_index_clause.
    def visitOid_index_clause(self, ctx:PlSqlParser.Oid_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#oid_clause.
    def visitOid_clause(self, ctx:PlSqlParser.Oid_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_properties.
    def visitObject_properties(self, ctx:PlSqlParser.Object_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_table_substitution.
    def visitObject_table_substitution(self, ctx:PlSqlParser.Object_table_substitutionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#relational_table.
    def visitRelational_table(self, ctx:PlSqlParser.Relational_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#relational_table_properties.
    def visitRelational_table_properties(self, ctx:PlSqlParser.Relational_table_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#relational_table_property.
    def visitRelational_table_property(self, ctx:PlSqlParser.Relational_table_propertyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#immutable_table_clauses.
    def visitImmutable_table_clauses(self, ctx:PlSqlParser.Immutable_table_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#immutable_table_no_drop_clause.
    def visitImmutable_table_no_drop_clause(self, ctx:PlSqlParser.Immutable_table_no_drop_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#immutable_table_no_delete_clause.
    def visitImmutable_table_no_delete_clause(self, ctx:PlSqlParser.Immutable_table_no_delete_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#blockchain_table_clauses.
    def visitBlockchain_table_clauses(self, ctx:PlSqlParser.Blockchain_table_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#blockchain_drop_table_clause.
    def visitBlockchain_drop_table_clause(self, ctx:PlSqlParser.Blockchain_drop_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#blockchain_row_retention_clause.
    def visitBlockchain_row_retention_clause(self, ctx:PlSqlParser.Blockchain_row_retention_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#blockchain_hash_and_data_format_clause.
    def visitBlockchain_hash_and_data_format_clause(self, ctx:PlSqlParser.Blockchain_hash_and_data_format_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#collation_name.
    def visitCollation_name(self, ctx:PlSqlParser.Collation_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_properties.
    def visitTable_properties(self, ctx:PlSqlParser.Table_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#read_only_clause.
    def visitRead_only_clause(self, ctx:PlSqlParser.Read_only_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#indexing_clause.
    def visitIndexing_clause(self, ctx:PlSqlParser.Indexing_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#attribute_clustering_clause.
    def visitAttribute_clustering_clause(self, ctx:PlSqlParser.Attribute_clustering_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#clustering_join.
    def visitClustering_join(self, ctx:PlSqlParser.Clustering_joinContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#clustering_join_item.
    def visitClustering_join_item(self, ctx:PlSqlParser.Clustering_join_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#equijoin_condition.
    def visitEquijoin_condition(self, ctx:PlSqlParser.Equijoin_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cluster_clause.
    def visitCluster_clause(self, ctx:PlSqlParser.Cluster_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#clustering_columns.
    def visitClustering_columns(self, ctx:PlSqlParser.Clustering_columnsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#clustering_column_group.
    def visitClustering_column_group(self, ctx:PlSqlParser.Clustering_column_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#yes_no.
    def visitYes_no(self, ctx:PlSqlParser.Yes_noContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#zonemap_clause.
    def visitZonemap_clause(self, ctx:PlSqlParser.Zonemap_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#logical_replication_clause.
    def visitLogical_replication_clause(self, ctx:PlSqlParser.Logical_replication_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_name.
    def visitTable_name(self, ctx:PlSqlParser.Table_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#relational_property.
    def visitRelational_property(self, ctx:PlSqlParser.Relational_propertyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_partitioning_clauses.
    def visitTable_partitioning_clauses(self, ctx:PlSqlParser.Table_partitioning_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#range_partitions.
    def visitRange_partitions(self, ctx:PlSqlParser.Range_partitionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#list_partitions.
    def visitList_partitions(self, ctx:PlSqlParser.List_partitionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hash_partitions.
    def visitHash_partitions(self, ctx:PlSqlParser.Hash_partitionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#individual_hash_partitions.
    def visitIndividual_hash_partitions(self, ctx:PlSqlParser.Individual_hash_partitionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hash_partitions_by_quantity.
    def visitHash_partitions_by_quantity(self, ctx:PlSqlParser.Hash_partitions_by_quantityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hash_partition_quantity.
    def visitHash_partition_quantity(self, ctx:PlSqlParser.Hash_partition_quantityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#composite_range_partitions.
    def visitComposite_range_partitions(self, ctx:PlSqlParser.Composite_range_partitionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#composite_list_partitions.
    def visitComposite_list_partitions(self, ctx:PlSqlParser.Composite_list_partitionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#composite_hash_partitions.
    def visitComposite_hash_partitions(self, ctx:PlSqlParser.Composite_hash_partitionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#reference_partitioning.
    def visitReference_partitioning(self, ctx:PlSqlParser.Reference_partitioningContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#reference_partition_desc.
    def visitReference_partition_desc(self, ctx:PlSqlParser.Reference_partition_descContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#system_partitioning.
    def visitSystem_partitioning(self, ctx:PlSqlParser.System_partitioningContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#range_partition_desc.
    def visitRange_partition_desc(self, ctx:PlSqlParser.Range_partition_descContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#list_partition_desc.
    def visitList_partition_desc(self, ctx:PlSqlParser.List_partition_descContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subpartition_template.
    def visitSubpartition_template(self, ctx:PlSqlParser.Subpartition_templateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hash_subpartition_quantity.
    def visitHash_subpartition_quantity(self, ctx:PlSqlParser.Hash_subpartition_quantityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subpartition_by_range.
    def visitSubpartition_by_range(self, ctx:PlSqlParser.Subpartition_by_rangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subpartition_by_list.
    def visitSubpartition_by_list(self, ctx:PlSqlParser.Subpartition_by_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subpartition_by_hash.
    def visitSubpartition_by_hash(self, ctx:PlSqlParser.Subpartition_by_hashContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subpartition_name.
    def visitSubpartition_name(self, ctx:PlSqlParser.Subpartition_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#range_subpartition_desc.
    def visitRange_subpartition_desc(self, ctx:PlSqlParser.Range_subpartition_descContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#list_subpartition_desc.
    def visitList_subpartition_desc(self, ctx:PlSqlParser.List_subpartition_descContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#individual_hash_subparts.
    def visitIndividual_hash_subparts(self, ctx:PlSqlParser.Individual_hash_subpartsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hash_subparts_by_quantity.
    def visitHash_subparts_by_quantity(self, ctx:PlSqlParser.Hash_subparts_by_quantityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#range_values_clause.
    def visitRange_values_clause(self, ctx:PlSqlParser.Range_values_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#range_values_list.
    def visitRange_values_list(self, ctx:PlSqlParser.Range_values_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#list_values_clause.
    def visitList_values_clause(self, ctx:PlSqlParser.List_values_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_partition_description.
    def visitTable_partition_description(self, ctx:PlSqlParser.Table_partition_descriptionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partitioning_storage_clause.
    def visitPartitioning_storage_clause(self, ctx:PlSqlParser.Partitioning_storage_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_partitioning_storage.
    def visitLob_partitioning_storage(self, ctx:PlSqlParser.Lob_partitioning_storageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#size_clause.
    def visitSize_clause(self, ctx:PlSqlParser.Size_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_compression.
    def visitTable_compression(self, ctx:PlSqlParser.Table_compressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inmemory_table_clause.
    def visitInmemory_table_clause(self, ctx:PlSqlParser.Inmemory_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inmemory_attributes.
    def visitInmemory_attributes(self, ctx:PlSqlParser.Inmemory_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inmemory_memcompress.
    def visitInmemory_memcompress(self, ctx:PlSqlParser.Inmemory_memcompressContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inmemory_priority.
    def visitInmemory_priority(self, ctx:PlSqlParser.Inmemory_priorityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inmemory_distribute.
    def visitInmemory_distribute(self, ctx:PlSqlParser.Inmemory_distributeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inmemory_duplicate.
    def visitInmemory_duplicate(self, ctx:PlSqlParser.Inmemory_duplicateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inmemory_column_clause.
    def visitInmemory_column_clause(self, ctx:PlSqlParser.Inmemory_column_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#physical_attributes_clause.
    def visitPhysical_attributes_clause(self, ctx:PlSqlParser.Physical_attributes_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#storage_clause.
    def visitStorage_clause(self, ctx:PlSqlParser.Storage_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#deferred_segment_creation.
    def visitDeferred_segment_creation(self, ctx:PlSqlParser.Deferred_segment_creationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#segment_attributes_clause.
    def visitSegment_attributes_clause(self, ctx:PlSqlParser.Segment_attributes_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#physical_properties.
    def visitPhysical_properties(self, ctx:PlSqlParser.Physical_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ilm_clause.
    def visitIlm_clause(self, ctx:PlSqlParser.Ilm_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ilm_policy_clause.
    def visitIlm_policy_clause(self, ctx:PlSqlParser.Ilm_policy_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ilm_compression_policy.
    def visitIlm_compression_policy(self, ctx:PlSqlParser.Ilm_compression_policyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ilm_tiering_policy.
    def visitIlm_tiering_policy(self, ctx:PlSqlParser.Ilm_tiering_policyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ilm_after_on.
    def visitIlm_after_on(self, ctx:PlSqlParser.Ilm_after_onContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#segment_group.
    def visitSegment_group(self, ctx:PlSqlParser.Segment_groupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ilm_inmemory_policy.
    def visitIlm_inmemory_policy(self, ctx:PlSqlParser.Ilm_inmemory_policyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ilm_time_period.
    def visitIlm_time_period(self, ctx:PlSqlParser.Ilm_time_periodContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#heap_org_table_clause.
    def visitHeap_org_table_clause(self, ctx:PlSqlParser.Heap_org_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_clause.
    def visitExternal_table_clause(self, ctx:PlSqlParser.External_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#access_driver_type.
    def visitAccess_driver_type(self, ctx:PlSqlParser.Access_driver_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_data_props.
    def visitExternal_table_data_props(self, ctx:PlSqlParser.External_table_data_propsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_data_format.
    def visitExternal_table_data_format(self, ctx:PlSqlParser.External_table_data_formatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_transform.
    def visitExternal_table_transform(self, ctx:PlSqlParser.External_table_transformContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_field.
    def visitExternal_table_field(self, ctx:PlSqlParser.External_table_fieldContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_field_list.
    def visitExternal_table_field_list(self, ctx:PlSqlParser.External_table_field_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_fields_clause.
    def visitExternal_table_fields_clause(self, ctx:PlSqlParser.External_table_fields_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_position_clause.
    def visitExternal_table_position_clause(self, ctx:PlSqlParser.External_table_position_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_datatype_clause.
    def visitExternal_table_datatype_clause(self, ctx:PlSqlParser.External_table_datatype_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_delimit_clause.
    def visitExternal_table_delimit_clause(self, ctx:PlSqlParser.External_table_delimit_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_trim_clause.
    def visitExternal_table_trim_clause(self, ctx:PlSqlParser.External_table_trim_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_date_format_clause.
    def visitExternal_table_date_format_clause(self, ctx:PlSqlParser.External_table_date_format_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_init_clause.
    def visitExternal_table_init_clause(self, ctx:PlSqlParser.External_table_init_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_condition_clause.
    def visitExternal_table_condition_clause(self, ctx:PlSqlParser.External_table_condition_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_lls_clause.
    def visitExternal_table_lls_clause(self, ctx:PlSqlParser.External_table_lls_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_records.
    def visitExternal_table_records(self, ctx:PlSqlParser.External_table_recordsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_record_options_clause.
    def visitExternal_table_record_options_clause(self, ctx:PlSqlParser.External_table_record_options_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_output_files.
    def visitExternal_table_output_files(self, ctx:PlSqlParser.External_table_output_filesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_fields.
    def visitExternal_table_fields(self, ctx:PlSqlParser.External_table_fieldsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_datapump.
    def visitExternal_table_datapump(self, ctx:PlSqlParser.External_table_datapumpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_hive.
    def visitExternal_table_hive(self, ctx:PlSqlParser.External_table_hiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_hive_parameter_map.
    def visitExternal_table_hive_parameter_map(self, ctx:PlSqlParser.External_table_hive_parameter_mapContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_hive_parameter_map_entry.
    def visitExternal_table_hive_parameter_map_entry(self, ctx:PlSqlParser.External_table_hive_parameter_map_entryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#external_table_directory.
    def visitExternal_table_directory(self, ctx:PlSqlParser.External_table_directoryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#row_movement_clause.
    def visitRow_movement_clause(self, ctx:PlSqlParser.Row_movement_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#flashback_archive_clause.
    def visitFlashback_archive_clause(self, ctx:PlSqlParser.Flashback_archive_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#log_grp.
    def visitLog_grp(self, ctx:PlSqlParser.Log_grpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#supplemental_table_logging.
    def visitSupplemental_table_logging(self, ctx:PlSqlParser.Supplemental_table_loggingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#supplemental_log_grp_clause.
    def visitSupplemental_log_grp_clause(self, ctx:PlSqlParser.Supplemental_log_grp_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#supplemental_id_key_clause.
    def visitSupplemental_id_key_clause(self, ctx:PlSqlParser.Supplemental_id_key_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#allocate_extent_clause.
    def visitAllocate_extent_clause(self, ctx:PlSqlParser.Allocate_extent_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#deallocate_unused_clause.
    def visitDeallocate_unused_clause(self, ctx:PlSqlParser.Deallocate_unused_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#shrink_clause.
    def visitShrink_clause(self, ctx:PlSqlParser.Shrink_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#records_per_block_clause.
    def visitRecords_per_block_clause(self, ctx:PlSqlParser.Records_per_block_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#upgrade_table_clause.
    def visitUpgrade_table_clause(self, ctx:PlSqlParser.Upgrade_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#truncate_table.
    def visitTruncate_table(self, ctx:PlSqlParser.Truncate_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_table.
    def visitDrop_table(self, ctx:PlSqlParser.Drop_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_tablespace.
    def visitDrop_tablespace(self, ctx:PlSqlParser.Drop_tablespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_tablespace_set.
    def visitDrop_tablespace_set(self, ctx:PlSqlParser.Drop_tablespace_setContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#including_contents_clause.
    def visitIncluding_contents_clause(self, ctx:PlSqlParser.Including_contents_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_view.
    def visitDrop_view(self, ctx:PlSqlParser.Drop_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#comment_on_column.
    def visitComment_on_column(self, ctx:PlSqlParser.Comment_on_columnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#enable_or_disable.
    def visitEnable_or_disable(self, ctx:PlSqlParser.Enable_or_disableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#allow_or_disallow.
    def visitAllow_or_disallow(self, ctx:PlSqlParser.Allow_or_disallowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_synonym.
    def visitAlter_synonym(self, ctx:PlSqlParser.Alter_synonymContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_synonym.
    def visitCreate_synonym(self, ctx:PlSqlParser.Create_synonymContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_synonym.
    def visitDrop_synonym(self, ctx:PlSqlParser.Drop_synonymContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_spfile.
    def visitCreate_spfile(self, ctx:PlSqlParser.Create_spfileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#spfile_name.
    def visitSpfile_name(self, ctx:PlSqlParser.Spfile_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pfile_name.
    def visitPfile_name(self, ctx:PlSqlParser.Pfile_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#comment_on_table.
    def visitComment_on_table(self, ctx:PlSqlParser.Comment_on_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#comment_on_materialized.
    def visitComment_on_materialized(self, ctx:PlSqlParser.Comment_on_materializedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_analytic_view.
    def visitAlter_analytic_view(self, ctx:PlSqlParser.Alter_analytic_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_add_cache_clause.
    def visitAlter_add_cache_clause(self, ctx:PlSqlParser.Alter_add_cache_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#levels_item.
    def visitLevels_item(self, ctx:PlSqlParser.Levels_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#measure_list.
    def visitMeasure_list(self, ctx:PlSqlParser.Measure_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_drop_cache_clause.
    def visitAlter_drop_cache_clause(self, ctx:PlSqlParser.Alter_drop_cache_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_attribute_dimension.
    def visitAlter_attribute_dimension(self, ctx:PlSqlParser.Alter_attribute_dimensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_audit_policy.
    def visitAlter_audit_policy(self, ctx:PlSqlParser.Alter_audit_policyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_cluster.
    def visitAlter_cluster(self, ctx:PlSqlParser.Alter_clusterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_analytic_view.
    def visitDrop_analytic_view(self, ctx:PlSqlParser.Drop_analytic_viewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_attribute_dimension.
    def visitDrop_attribute_dimension(self, ctx:PlSqlParser.Drop_attribute_dimensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_audit_policy.
    def visitDrop_audit_policy(self, ctx:PlSqlParser.Drop_audit_policyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_flashback_archive.
    def visitDrop_flashback_archive(self, ctx:PlSqlParser.Drop_flashback_archiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_cluster.
    def visitDrop_cluster(self, ctx:PlSqlParser.Drop_clusterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_context.
    def visitDrop_context(self, ctx:PlSqlParser.Drop_contextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_directory.
    def visitDrop_directory(self, ctx:PlSqlParser.Drop_directoryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_diskgroup.
    def visitDrop_diskgroup(self, ctx:PlSqlParser.Drop_diskgroupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_edition.
    def visitDrop_edition(self, ctx:PlSqlParser.Drop_editionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#truncate_cluster.
    def visitTruncate_cluster(self, ctx:PlSqlParser.Truncate_clusterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cache_or_nocache.
    def visitCache_or_nocache(self, ctx:PlSqlParser.Cache_or_nocacheContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#database_name.
    def visitDatabase_name(self, ctx:PlSqlParser.Database_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_database.
    def visitAlter_database(self, ctx:PlSqlParser.Alter_databaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#database_clause.
    def visitDatabase_clause(self, ctx:PlSqlParser.Database_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#startup_clauses.
    def visitStartup_clauses(self, ctx:PlSqlParser.Startup_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#resetlogs_or_noresetlogs.
    def visitResetlogs_or_noresetlogs(self, ctx:PlSqlParser.Resetlogs_or_noresetlogsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#upgrade_or_downgrade.
    def visitUpgrade_or_downgrade(self, ctx:PlSqlParser.Upgrade_or_downgradeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#recovery_clauses.
    def visitRecovery_clauses(self, ctx:PlSqlParser.Recovery_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#begin_or_end.
    def visitBegin_or_end(self, ctx:PlSqlParser.Begin_or_endContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#general_recovery.
    def visitGeneral_recovery(self, ctx:PlSqlParser.General_recoveryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#full_database_recovery.
    def visitFull_database_recovery(self, ctx:PlSqlParser.Full_database_recoveryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partial_database_recovery.
    def visitPartial_database_recovery(self, ctx:PlSqlParser.Partial_database_recoveryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partial_database_recovery_10g.
    def visitPartial_database_recovery_10g(self, ctx:PlSqlParser.Partial_database_recovery_10gContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#managed_standby_recovery.
    def visitManaged_standby_recovery(self, ctx:PlSqlParser.Managed_standby_recoveryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#db_name.
    def visitDb_name(self, ctx:PlSqlParser.Db_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#database_file_clauses.
    def visitDatabase_file_clauses(self, ctx:PlSqlParser.Database_file_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_datafile_clause.
    def visitCreate_datafile_clause(self, ctx:PlSqlParser.Create_datafile_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_datafile_clause.
    def visitAlter_datafile_clause(self, ctx:PlSqlParser.Alter_datafile_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_tempfile_clause.
    def visitAlter_tempfile_clause(self, ctx:PlSqlParser.Alter_tempfile_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#move_datafile_clause.
    def visitMove_datafile_clause(self, ctx:PlSqlParser.Move_datafile_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#logfile_clauses.
    def visitLogfile_clauses(self, ctx:PlSqlParser.Logfile_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_logfile_clauses.
    def visitAdd_logfile_clauses(self, ctx:PlSqlParser.Add_logfile_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#group_redo_logfile.
    def visitGroup_redo_logfile(self, ctx:PlSqlParser.Group_redo_logfileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_logfile_clauses.
    def visitDrop_logfile_clauses(self, ctx:PlSqlParser.Drop_logfile_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#switch_logfile_clause.
    def visitSwitch_logfile_clause(self, ctx:PlSqlParser.Switch_logfile_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#supplemental_db_logging.
    def visitSupplemental_db_logging(self, ctx:PlSqlParser.Supplemental_db_loggingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_or_drop.
    def visitAdd_or_drop(self, ctx:PlSqlParser.Add_or_dropContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#supplemental_plsql_clause.
    def visitSupplemental_plsql_clause(self, ctx:PlSqlParser.Supplemental_plsql_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#logfile_descriptor.
    def visitLogfile_descriptor(self, ctx:PlSqlParser.Logfile_descriptorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#controlfile_clauses.
    def visitControlfile_clauses(self, ctx:PlSqlParser.Controlfile_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#trace_file_clause.
    def visitTrace_file_clause(self, ctx:PlSqlParser.Trace_file_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#standby_database_clauses.
    def visitStandby_database_clauses(self, ctx:PlSqlParser.Standby_database_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#activate_standby_db_clause.
    def visitActivate_standby_db_clause(self, ctx:PlSqlParser.Activate_standby_db_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#maximize_standby_db_clause.
    def visitMaximize_standby_db_clause(self, ctx:PlSqlParser.Maximize_standby_db_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#register_logfile_clause.
    def visitRegister_logfile_clause(self, ctx:PlSqlParser.Register_logfile_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#commit_switchover_clause.
    def visitCommit_switchover_clause(self, ctx:PlSqlParser.Commit_switchover_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#start_standby_clause.
    def visitStart_standby_clause(self, ctx:PlSqlParser.Start_standby_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#stop_standby_clause.
    def visitStop_standby_clause(self, ctx:PlSqlParser.Stop_standby_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#convert_database_clause.
    def visitConvert_database_clause(self, ctx:PlSqlParser.Convert_database_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_settings_clause.
    def visitDefault_settings_clause(self, ctx:PlSqlParser.Default_settings_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#set_time_zone_clause.
    def visitSet_time_zone_clause(self, ctx:PlSqlParser.Set_time_zone_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#instance_clauses.
    def visitInstance_clauses(self, ctx:PlSqlParser.Instance_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#security_clause.
    def visitSecurity_clause(self, ctx:PlSqlParser.Security_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#domain.
    def visitDomain(self, ctx:PlSqlParser.DomainContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#database.
    def visitDatabase(self, ctx:PlSqlParser.DatabaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#edition_name.
    def visitEdition_name(self, ctx:PlSqlParser.Edition_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#filenumber.
    def visitFilenumber(self, ctx:PlSqlParser.FilenumberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#filename.
    def visitFilename(self, ctx:PlSqlParser.FilenameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#prepare_clause.
    def visitPrepare_clause(self, ctx:PlSqlParser.Prepare_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_mirror_clause.
    def visitDrop_mirror_clause(self, ctx:PlSqlParser.Drop_mirror_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lost_write_protection.
    def visitLost_write_protection(self, ctx:PlSqlParser.Lost_write_protectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cdb_fleet_clauses.
    def visitCdb_fleet_clauses(self, ctx:PlSqlParser.Cdb_fleet_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lead_cdb_clause.
    def visitLead_cdb_clause(self, ctx:PlSqlParser.Lead_cdb_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lead_cdb_uri_clause.
    def visitLead_cdb_uri_clause(self, ctx:PlSqlParser.Lead_cdb_uri_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#property_clauses.
    def visitProperty_clauses(self, ctx:PlSqlParser.Property_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#replay_upgrade_clauses.
    def visitReplay_upgrade_clauses(self, ctx:PlSqlParser.Replay_upgrade_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_database_link.
    def visitAlter_database_link(self, ctx:PlSqlParser.Alter_database_linkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#password_value.
    def visitPassword_value(self, ctx:PlSqlParser.Password_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#link_authentication.
    def visitLink_authentication(self, ctx:PlSqlParser.Link_authenticationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_schema.
    def visitCreate_schema(self, ctx:PlSqlParser.Create_schemaContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_database.
    def visitCreate_database(self, ctx:PlSqlParser.Create_databaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#database_logging_clauses.
    def visitDatabase_logging_clauses(self, ctx:PlSqlParser.Database_logging_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#database_logging_sub_clause.
    def visitDatabase_logging_sub_clause(self, ctx:PlSqlParser.Database_logging_sub_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_clauses.
    def visitTablespace_clauses(self, ctx:PlSqlParser.Tablespace_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#enable_pluggable_database.
    def visitEnable_pluggable_database(self, ctx:PlSqlParser.Enable_pluggable_databaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#file_name_convert.
    def visitFile_name_convert(self, ctx:PlSqlParser.File_name_convertContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#filename_convert_sub_clause.
    def visitFilename_convert_sub_clause(self, ctx:PlSqlParser.Filename_convert_sub_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace_datafile_clauses.
    def visitTablespace_datafile_clauses(self, ctx:PlSqlParser.Tablespace_datafile_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#undo_mode_clause.
    def visitUndo_mode_clause(self, ctx:PlSqlParser.Undo_mode_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_tablespace.
    def visitDefault_tablespace(self, ctx:PlSqlParser.Default_tablespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_temp_tablespace.
    def visitDefault_temp_tablespace(self, ctx:PlSqlParser.Default_temp_tablespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#undo_tablespace.
    def visitUndo_tablespace(self, ctx:PlSqlParser.Undo_tablespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_database.
    def visitDrop_database(self, ctx:PlSqlParser.Drop_databaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#create_database_link.
    def visitCreate_database_link(self, ctx:PlSqlParser.Create_database_linkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_database_link.
    def visitDrop_database_link(self, ctx:PlSqlParser.Drop_database_linkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_tablespace_set.
    def visitAlter_tablespace_set(self, ctx:PlSqlParser.Alter_tablespace_setContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_tablespace_attrs.
    def visitAlter_tablespace_attrs(self, ctx:PlSqlParser.Alter_tablespace_attrsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_tablespace_encryption.
    def visitAlter_tablespace_encryption(self, ctx:PlSqlParser.Alter_tablespace_encryptionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ts_file_name_convert.
    def visitTs_file_name_convert(self, ctx:PlSqlParser.Ts_file_name_convertContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_role.
    def visitAlter_role(self, ctx:PlSqlParser.Alter_roleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#role_identified_clause.
    def visitRole_identified_clause(self, ctx:PlSqlParser.Role_identified_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_table.
    def visitAlter_table(self, ctx:PlSqlParser.Alter_tableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#memoptimize_read_write_clause.
    def visitMemoptimize_read_write_clause(self, ctx:PlSqlParser.Memoptimize_read_write_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_table_properties.
    def visitAlter_table_properties(self, ctx:PlSqlParser.Alter_table_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_table_partitioning.
    def visitAlter_table_partitioning(self, ctx:PlSqlParser.Alter_table_partitioningContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_table_partition.
    def visitAdd_table_partition(self, ctx:PlSqlParser.Add_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_table_partition.
    def visitDrop_table_partition(self, ctx:PlSqlParser.Drop_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#merge_table_partition.
    def visitMerge_table_partition(self, ctx:PlSqlParser.Merge_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_table_partition.
    def visitModify_table_partition(self, ctx:PlSqlParser.Modify_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#split_table_partition.
    def visitSplit_table_partition(self, ctx:PlSqlParser.Split_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#truncate_table_partition.
    def visitTruncate_table_partition(self, ctx:PlSqlParser.Truncate_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#exchange_table_partition.
    def visitExchange_table_partition(self, ctx:PlSqlParser.Exchange_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#coalesce_table_partition.
    def visitCoalesce_table_partition(self, ctx:PlSqlParser.Coalesce_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_interval_partition.
    def visitAlter_interval_partition(self, ctx:PlSqlParser.Alter_interval_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#move_table_partition.
    def visitMove_table_partition(self, ctx:PlSqlParser.Move_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#filter_condition.
    def visitFilter_condition(self, ctx:PlSqlParser.Filter_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rename_table_partition.
    def visitRename_table_partition(self, ctx:PlSqlParser.Rename_table_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partition_extended_names.
    def visitPartition_extended_names(self, ctx:PlSqlParser.Partition_extended_namesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subpartition_extended_names.
    def visitSubpartition_extended_names(self, ctx:PlSqlParser.Subpartition_extended_namesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_table_properties_1.
    def visitAlter_table_properties_1(self, ctx:PlSqlParser.Alter_table_properties_1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_iot_clauses.
    def visitAlter_iot_clauses(self, ctx:PlSqlParser.Alter_iot_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_mapping_table_clause.
    def visitAlter_mapping_table_clause(self, ctx:PlSqlParser.Alter_mapping_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#alter_overflow_clause.
    def visitAlter_overflow_clause(self, ctx:PlSqlParser.Alter_overflow_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_overflow_clause.
    def visitAdd_overflow_clause(self, ctx:PlSqlParser.Add_overflow_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#update_index_clauses.
    def visitUpdate_index_clauses(self, ctx:PlSqlParser.Update_index_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#update_global_index_clause.
    def visitUpdate_global_index_clause(self, ctx:PlSqlParser.Update_global_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#update_all_indexes_clause.
    def visitUpdate_all_indexes_clause(self, ctx:PlSqlParser.Update_all_indexes_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#update_all_indexes_index_clause.
    def visitUpdate_all_indexes_index_clause(self, ctx:PlSqlParser.Update_all_indexes_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#update_index_partition.
    def visitUpdate_index_partition(self, ctx:PlSqlParser.Update_index_partitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#update_index_subpartition.
    def visitUpdate_index_subpartition(self, ctx:PlSqlParser.Update_index_subpartitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#enable_disable_clause.
    def visitEnable_disable_clause(self, ctx:PlSqlParser.Enable_disable_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#using_index_clause.
    def visitUsing_index_clause(self, ctx:PlSqlParser.Using_index_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_attributes.
    def visitIndex_attributes(self, ctx:PlSqlParser.Index_attributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sort_or_nosort.
    def visitSort_or_nosort(self, ctx:PlSqlParser.Sort_or_nosortContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#exceptions_clause.
    def visitExceptions_clause(self, ctx:PlSqlParser.Exceptions_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#move_table_clause.
    def visitMove_table_clause(self, ctx:PlSqlParser.Move_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_org_table_clause.
    def visitIndex_org_table_clause(self, ctx:PlSqlParser.Index_org_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#mapping_table_clause.
    def visitMapping_table_clause(self, ctx:PlSqlParser.Mapping_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#key_compression.
    def visitKey_compression(self, ctx:PlSqlParser.Key_compressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_org_overflow_clause.
    def visitIndex_org_overflow_clause(self, ctx:PlSqlParser.Index_org_overflow_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_clauses.
    def visitColumn_clauses(self, ctx:PlSqlParser.Column_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_collection_retrieval.
    def visitModify_collection_retrieval(self, ctx:PlSqlParser.Modify_collection_retrievalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#collection_item.
    def visitCollection_item(self, ctx:PlSqlParser.Collection_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rename_column_clause.
    def visitRename_column_clause(self, ctx:PlSqlParser.Rename_column_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#old_column_name.
    def visitOld_column_name(self, ctx:PlSqlParser.Old_column_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#new_column_name.
    def visitNew_column_name(self, ctx:PlSqlParser.New_column_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_modify_drop_column_clauses.
    def visitAdd_modify_drop_column_clauses(self, ctx:PlSqlParser.Add_modify_drop_column_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_column_clause.
    def visitDrop_column_clause(self, ctx:PlSqlParser.Drop_column_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_column_clauses.
    def visitModify_column_clauses(self, ctx:PlSqlParser.Modify_column_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_col_properties.
    def visitModify_col_properties(self, ctx:PlSqlParser.Modify_col_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_col_visibility.
    def visitModify_col_visibility(self, ctx:PlSqlParser.Modify_col_visibilityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_col_substitutable.
    def visitModify_col_substitutable(self, ctx:PlSqlParser.Modify_col_substitutableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_column_clause.
    def visitAdd_column_clause(self, ctx:PlSqlParser.Add_column_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#varray_col_properties.
    def visitVarray_col_properties(self, ctx:PlSqlParser.Varray_col_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#varray_storage_clause.
    def visitVarray_storage_clause(self, ctx:PlSqlParser.Varray_storage_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_segname.
    def visitLob_segname(self, ctx:PlSqlParser.Lob_segnameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_item.
    def visitLob_item(self, ctx:PlSqlParser.Lob_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_storage_parameters.
    def visitLob_storage_parameters(self, ctx:PlSqlParser.Lob_storage_parametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_storage_clause.
    def visitLob_storage_clause(self, ctx:PlSqlParser.Lob_storage_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_lob_storage_clause.
    def visitModify_lob_storage_clause(self, ctx:PlSqlParser.Modify_lob_storage_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#modify_lob_parameters.
    def visitModify_lob_parameters(self, ctx:PlSqlParser.Modify_lob_parametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_parameters.
    def visitLob_parameters(self, ctx:PlSqlParser.Lob_parametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_deduplicate_clause.
    def visitLob_deduplicate_clause(self, ctx:PlSqlParser.Lob_deduplicate_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_compression_clause.
    def visitLob_compression_clause(self, ctx:PlSqlParser.Lob_compression_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_retention_clause.
    def visitLob_retention_clause(self, ctx:PlSqlParser.Lob_retention_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#encryption_spec.
    def visitEncryption_spec(self, ctx:PlSqlParser.Encryption_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tablespace.
    def visitTablespace(self, ctx:PlSqlParser.TablespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#varray_item.
    def visitVarray_item(self, ctx:PlSqlParser.Varray_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_properties.
    def visitColumn_properties(self, ctx:PlSqlParser.Column_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lob_partition_storage.
    def visitLob_partition_storage(self, ctx:PlSqlParser.Lob_partition_storageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#period_definition.
    def visitPeriod_definition(self, ctx:PlSqlParser.Period_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#start_time_column.
    def visitStart_time_column(self, ctx:PlSqlParser.Start_time_columnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#end_time_column.
    def visitEnd_time_column(self, ctx:PlSqlParser.End_time_columnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_definition.
    def visitColumn_definition(self, ctx:PlSqlParser.Column_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_collation_name.
    def visitColumn_collation_name(self, ctx:PlSqlParser.Column_collation_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#identity_clause.
    def visitIdentity_clause(self, ctx:PlSqlParser.Identity_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#identity_options_parentheses.
    def visitIdentity_options_parentheses(self, ctx:PlSqlParser.Identity_options_parenthesesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#identity_options.
    def visitIdentity_options(self, ctx:PlSqlParser.Identity_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#virtual_column_definition.
    def visitVirtual_column_definition(self, ctx:PlSqlParser.Virtual_column_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#virtual_column_expression.
    def visitVirtual_column_expression(self, ctx:PlSqlParser.Virtual_column_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#autogenerated_sequence_definition.
    def visitAutogenerated_sequence_definition(self, ctx:PlSqlParser.Autogenerated_sequence_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#by_user_for_statistics_clause.
    def visitBy_user_for_statistics_clause(self, ctx:PlSqlParser.By_user_for_statistics_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#evaluation_edition_clause.
    def visitEvaluation_edition_clause(self, ctx:PlSqlParser.Evaluation_edition_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#nested_table_col_properties.
    def visitNested_table_col_properties(self, ctx:PlSqlParser.Nested_table_col_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#nested_item.
    def visitNested_item(self, ctx:PlSqlParser.Nested_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#substitutable_column_clause.
    def visitSubstitutable_column_clause(self, ctx:PlSqlParser.Substitutable_column_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partition_name.
    def visitPartition_name(self, ctx:PlSqlParser.Partition_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#supplemental_logging_props.
    def visitSupplemental_logging_props(self, ctx:PlSqlParser.Supplemental_logging_propsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_type_col_properties.
    def visitObject_type_col_properties(self, ctx:PlSqlParser.Object_type_col_propertiesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#constraint_clauses.
    def visitConstraint_clauses(self, ctx:PlSqlParser.Constraint_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#old_constraint_name.
    def visitOld_constraint_name(self, ctx:PlSqlParser.Old_constraint_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#new_constraint_name.
    def visitNew_constraint_name(self, ctx:PlSqlParser.New_constraint_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#drop_constraint_clause.
    def visitDrop_constraint_clause(self, ctx:PlSqlParser.Drop_constraint_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#check_constraint.
    def visitCheck_constraint(self, ctx:PlSqlParser.Check_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#foreign_key_clause.
    def visitForeign_key_clause(self, ctx:PlSqlParser.Foreign_key_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#references_clause.
    def visitReferences_clause(self, ctx:PlSqlParser.References_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#on_delete_clause.
    def visitOn_delete_clause(self, ctx:PlSqlParser.On_delete_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#anonymous_block.
    def visitAnonymous_block(self, ctx:PlSqlParser.Anonymous_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#invoker_rights_clause.
    def visitInvoker_rights_clause(self, ctx:PlSqlParser.Invoker_rights_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#call_spec.
    def visitCall_spec(self, ctx:PlSqlParser.Call_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#java_spec.
    def visitJava_spec(self, ctx:PlSqlParser.Java_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#c_spec.
    def visitC_spec(self, ctx:PlSqlParser.C_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#c_agent_in_clause.
    def visitC_agent_in_clause(self, ctx:PlSqlParser.C_agent_in_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#c_parameters_clause.
    def visitC_parameters_clause(self, ctx:PlSqlParser.C_parameters_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#c_external_parameter.
    def visitC_external_parameter(self, ctx:PlSqlParser.C_external_parameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#c_property.
    def visitC_property(self, ctx:PlSqlParser.C_propertyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#parameter.
    def visitParameter(self, ctx:PlSqlParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#default_value_part.
    def visitDefault_value_part(self, ctx:PlSqlParser.Default_value_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#seq_of_declare_specs.
    def visitSeq_of_declare_specs(self, ctx:PlSqlParser.Seq_of_declare_specsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#declare_spec.
    def visitDeclare_spec(self, ctx:PlSqlParser.Declare_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#variable_declaration.
    def visitVariable_declaration(self, ctx:PlSqlParser.Variable_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subtype_declaration.
    def visitSubtype_declaration(self, ctx:PlSqlParser.Subtype_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cursor_declaration.
    def visitCursor_declaration(self, ctx:PlSqlParser.Cursor_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#parameter_spec.
    def visitParameter_spec(self, ctx:PlSqlParser.Parameter_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#exception_declaration.
    def visitException_declaration(self, ctx:PlSqlParser.Exception_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pragma_declaration.
    def visitPragma_declaration(self, ctx:PlSqlParser.Pragma_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#record_type_def.
    def visitRecord_type_def(self, ctx:PlSqlParser.Record_type_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#field_spec.
    def visitField_spec(self, ctx:PlSqlParser.Field_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#ref_cursor_type_def.
    def visitRef_cursor_type_def(self, ctx:PlSqlParser.Ref_cursor_type_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_declaration.
    def visitType_declaration(self, ctx:PlSqlParser.Type_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_type_def.
    def visitTable_type_def(self, ctx:PlSqlParser.Table_type_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_indexed_by_part.
    def visitTable_indexed_by_part(self, ctx:PlSqlParser.Table_indexed_by_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#varray_type_def.
    def visitVarray_type_def(self, ctx:PlSqlParser.Varray_type_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#seq_of_statements.
    def visitSeq_of_statements(self, ctx:PlSqlParser.Seq_of_statementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#label_declaration.
    def visitLabel_declaration(self, ctx:PlSqlParser.Label_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#statement.
    def visitStatement(self, ctx:PlSqlParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#assignment_statement.
    def visitAssignment_statement(self, ctx:PlSqlParser.Assignment_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#continue_statement.
    def visitContinue_statement(self, ctx:PlSqlParser.Continue_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#exit_statement.
    def visitExit_statement(self, ctx:PlSqlParser.Exit_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#goto_statement.
    def visitGoto_statement(self, ctx:PlSqlParser.Goto_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#if_statement.
    def visitIf_statement(self, ctx:PlSqlParser.If_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#elsif_part.
    def visitElsif_part(self, ctx:PlSqlParser.Elsif_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#else_part.
    def visitElse_part(self, ctx:PlSqlParser.Else_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#loop_statement.
    def visitLoop_statement(self, ctx:PlSqlParser.Loop_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cursor_loop_param.
    def visitCursor_loop_param(self, ctx:PlSqlParser.Cursor_loop_paramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#forall_statement.
    def visitForall_statement(self, ctx:PlSqlParser.Forall_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#bounds_clause.
    def visitBounds_clause(self, ctx:PlSqlParser.Bounds_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#between_bound.
    def visitBetween_bound(self, ctx:PlSqlParser.Between_boundContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lower_bound.
    def visitLower_bound(self, ctx:PlSqlParser.Lower_boundContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#upper_bound.
    def visitUpper_bound(self, ctx:PlSqlParser.Upper_boundContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#null_statement.
    def visitNull_statement(self, ctx:PlSqlParser.Null_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#raise_statement.
    def visitRaise_statement(self, ctx:PlSqlParser.Raise_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#return_statement.
    def visitReturn_statement(self, ctx:PlSqlParser.Return_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#call_statement.
    def visitCall_statement(self, ctx:PlSqlParser.Call_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pipe_row_statement.
    def visitPipe_row_statement(self, ctx:PlSqlParser.Pipe_row_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#selection_directive.
    def visitSelection_directive(self, ctx:PlSqlParser.Selection_directiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#error_directive.
    def visitError_directive(self, ctx:PlSqlParser.Error_directiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#selection_directive_body.
    def visitSelection_directive_body(self, ctx:PlSqlParser.Selection_directive_bodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#body.
    def visitBody(self, ctx:PlSqlParser.BodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#exception_handler.
    def visitException_handler(self, ctx:PlSqlParser.Exception_handlerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#trigger_block.
    def visitTrigger_block(self, ctx:PlSqlParser.Trigger_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tps_block.
    def visitTps_block(self, ctx:PlSqlParser.Tps_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#block.
    def visitBlock(self, ctx:PlSqlParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sql_statement.
    def visitSql_statement(self, ctx:PlSqlParser.Sql_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#execute_immediate.
    def visitExecute_immediate(self, ctx:PlSqlParser.Execute_immediateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dynamic_returning_clause.
    def visitDynamic_returning_clause(self, ctx:PlSqlParser.Dynamic_returning_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#data_manipulation_language_statements.
    def visitData_manipulation_language_statements(self, ctx:PlSqlParser.Data_manipulation_language_statementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cursor_manipulation_statements.
    def visitCursor_manipulation_statements(self, ctx:PlSqlParser.Cursor_manipulation_statementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#close_statement.
    def visitClose_statement(self, ctx:PlSqlParser.Close_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#open_statement.
    def visitOpen_statement(self, ctx:PlSqlParser.Open_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#fetch_statement.
    def visitFetch_statement(self, ctx:PlSqlParser.Fetch_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#variable_or_collection.
    def visitVariable_or_collection(self, ctx:PlSqlParser.Variable_or_collectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#open_for_statement.
    def visitOpen_for_statement(self, ctx:PlSqlParser.Open_for_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#transaction_control_statements.
    def visitTransaction_control_statements(self, ctx:PlSqlParser.Transaction_control_statementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#set_transaction_command.
    def visitSet_transaction_command(self, ctx:PlSqlParser.Set_transaction_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#set_constraint_command.
    def visitSet_constraint_command(self, ctx:PlSqlParser.Set_constraint_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#commit_statement.
    def visitCommit_statement(self, ctx:PlSqlParser.Commit_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#write_clause.
    def visitWrite_clause(self, ctx:PlSqlParser.Write_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rollback_statement.
    def visitRollback_statement(self, ctx:PlSqlParser.Rollback_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#savepoint_statement.
    def visitSavepoint_statement(self, ctx:PlSqlParser.Savepoint_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#collection_method_call.
    def visitCollection_method_call(self, ctx:PlSqlParser.Collection_method_callContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#explain_statement.
    def visitExplain_statement(self, ctx:PlSqlParser.Explain_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#select_only_statement.
    def visitSelect_only_statement(self, ctx:PlSqlParser.Select_only_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#select_statement.
    def visitSelect_statement(self, ctx:PlSqlParser.Select_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#with_clause.
    def visitWith_clause(self, ctx:PlSqlParser.With_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#with_factoring_clause.
    def visitWith_factoring_clause(self, ctx:PlSqlParser.With_factoring_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subquery_factoring_clause.
    def visitSubquery_factoring_clause(self, ctx:PlSqlParser.Subquery_factoring_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#search_clause.
    def visitSearch_clause(self, ctx:PlSqlParser.Search_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cycle_clause.
    def visitCycle_clause(self, ctx:PlSqlParser.Cycle_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subav_factoring_clause.
    def visitSubav_factoring_clause(self, ctx:PlSqlParser.Subav_factoring_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subav_clause.
    def visitSubav_clause(self, ctx:PlSqlParser.Subav_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hierarchies_clause.
    def visitHierarchies_clause(self, ctx:PlSqlParser.Hierarchies_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#filter_clauses.
    def visitFilter_clauses(self, ctx:PlSqlParser.Filter_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#filter_clause.
    def visitFilter_clause(self, ctx:PlSqlParser.Filter_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_calcs_clause.
    def visitAdd_calcs_clause(self, ctx:PlSqlParser.Add_calcs_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#add_calc_meas_clause.
    def visitAdd_calc_meas_clause(self, ctx:PlSqlParser.Add_calc_meas_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subquery.
    def visitSubquery(self, ctx:PlSqlParser.SubqueryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subquery_basic_elements.
    def visitSubquery_basic_elements(self, ctx:PlSqlParser.Subquery_basic_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subquery_operation_part.
    def visitSubquery_operation_part(self, ctx:PlSqlParser.Subquery_operation_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#query_block.
    def visitQuery_block(self, ctx:PlSqlParser.Query_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#selected_list.
    def visitSelected_list(self, ctx:PlSqlParser.Selected_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#from_clause.
    def visitFrom_clause(self, ctx:PlSqlParser.From_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#select_list_elements.
    def visitSelect_list_elements(self, ctx:PlSqlParser.Select_list_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_ref_list.
    def visitTable_ref_list(self, ctx:PlSqlParser.Table_ref_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_ref.
    def visitTable_ref(self, ctx:PlSqlParser.Table_refContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_ref_aux.
    def visitTable_ref_aux(self, ctx:PlSqlParser.Table_ref_auxContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_ref_aux_internal_one.
    def visitTable_ref_aux_internal_one(self, ctx:PlSqlParser.Table_ref_aux_internal_oneContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_ref_aux_internal_two.
    def visitTable_ref_aux_internal_two(self, ctx:PlSqlParser.Table_ref_aux_internal_twoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_ref_aux_internal_thre.
    def visitTable_ref_aux_internal_thre(self, ctx:PlSqlParser.Table_ref_aux_internal_threContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#join_clause.
    def visitJoin_clause(self, ctx:PlSqlParser.Join_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#join_on_part.
    def visitJoin_on_part(self, ctx:PlSqlParser.Join_on_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#join_using_part.
    def visitJoin_using_part(self, ctx:PlSqlParser.Join_using_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#outer_join_type.
    def visitOuter_join_type(self, ctx:PlSqlParser.Outer_join_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#query_partition_clause.
    def visitQuery_partition_clause(self, ctx:PlSqlParser.Query_partition_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#flashback_query_clause.
    def visitFlashback_query_clause(self, ctx:PlSqlParser.Flashback_query_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pivot_clause.
    def visitPivot_clause(self, ctx:PlSqlParser.Pivot_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pivot_element.
    def visitPivot_element(self, ctx:PlSqlParser.Pivot_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pivot_for_clause.
    def visitPivot_for_clause(self, ctx:PlSqlParser.Pivot_for_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pivot_in_clause.
    def visitPivot_in_clause(self, ctx:PlSqlParser.Pivot_in_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pivot_in_clause_element.
    def visitPivot_in_clause_element(self, ctx:PlSqlParser.Pivot_in_clause_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#pivot_in_clause_elements.
    def visitPivot_in_clause_elements(self, ctx:PlSqlParser.Pivot_in_clause_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unpivot_clause.
    def visitUnpivot_clause(self, ctx:PlSqlParser.Unpivot_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unpivot_in_clause.
    def visitUnpivot_in_clause(self, ctx:PlSqlParser.Unpivot_in_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unpivot_in_elements.
    def visitUnpivot_in_elements(self, ctx:PlSqlParser.Unpivot_in_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#hierarchical_query_clause.
    def visitHierarchical_query_clause(self, ctx:PlSqlParser.Hierarchical_query_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#start_part.
    def visitStart_part(self, ctx:PlSqlParser.Start_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#group_by_clause.
    def visitGroup_by_clause(self, ctx:PlSqlParser.Group_by_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#group_by_elements.
    def visitGroup_by_elements(self, ctx:PlSqlParser.Group_by_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rollup_cube_clause.
    def visitRollup_cube_clause(self, ctx:PlSqlParser.Rollup_cube_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#grouping_sets_clause.
    def visitGrouping_sets_clause(self, ctx:PlSqlParser.Grouping_sets_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#grouping_sets_elements.
    def visitGrouping_sets_elements(self, ctx:PlSqlParser.Grouping_sets_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#having_clause.
    def visitHaving_clause(self, ctx:PlSqlParser.Having_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_clause.
    def visitModel_clause(self, ctx:PlSqlParser.Model_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cell_reference_options.
    def visitCell_reference_options(self, ctx:PlSqlParser.Cell_reference_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#return_rows_clause.
    def visitReturn_rows_clause(self, ctx:PlSqlParser.Return_rows_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#reference_model.
    def visitReference_model(self, ctx:PlSqlParser.Reference_modelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#main_model.
    def visitMain_model(self, ctx:PlSqlParser.Main_modelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_column_clauses.
    def visitModel_column_clauses(self, ctx:PlSqlParser.Model_column_clausesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_column_partition_part.
    def visitModel_column_partition_part(self, ctx:PlSqlParser.Model_column_partition_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_column_list.
    def visitModel_column_list(self, ctx:PlSqlParser.Model_column_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_column.
    def visitModel_column(self, ctx:PlSqlParser.Model_columnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_rules_clause.
    def visitModel_rules_clause(self, ctx:PlSqlParser.Model_rules_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_rules_part.
    def visitModel_rules_part(self, ctx:PlSqlParser.Model_rules_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_rules_element.
    def visitModel_rules_element(self, ctx:PlSqlParser.Model_rules_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cell_assignment.
    def visitCell_assignment(self, ctx:PlSqlParser.Cell_assignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_iterate_clause.
    def visitModel_iterate_clause(self, ctx:PlSqlParser.Model_iterate_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#until_part.
    def visitUntil_part(self, ctx:PlSqlParser.Until_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#order_by_clause.
    def visitOrder_by_clause(self, ctx:PlSqlParser.Order_by_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#order_by_elements.
    def visitOrder_by_elements(self, ctx:PlSqlParser.Order_by_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#offset_clause.
    def visitOffset_clause(self, ctx:PlSqlParser.Offset_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#fetch_clause.
    def visitFetch_clause(self, ctx:PlSqlParser.Fetch_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#for_update_clause.
    def visitFor_update_clause(self, ctx:PlSqlParser.For_update_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#for_update_of_part.
    def visitFor_update_of_part(self, ctx:PlSqlParser.For_update_of_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#for_update_options.
    def visitFor_update_options(self, ctx:PlSqlParser.For_update_optionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#update_statement.
    def visitUpdate_statement(self, ctx:PlSqlParser.Update_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#update_set_clause.
    def visitUpdate_set_clause(self, ctx:PlSqlParser.Update_set_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_based_update_set_clause.
    def visitColumn_based_update_set_clause(self, ctx:PlSqlParser.Column_based_update_set_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#delete_statement.
    def visitDelete_statement(self, ctx:PlSqlParser.Delete_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#insert_statement.
    def visitInsert_statement(self, ctx:PlSqlParser.Insert_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#single_table_insert.
    def visitSingle_table_insert(self, ctx:PlSqlParser.Single_table_insertContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#multi_table_insert.
    def visitMulti_table_insert(self, ctx:PlSqlParser.Multi_table_insertContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#multi_table_element.
    def visitMulti_table_element(self, ctx:PlSqlParser.Multi_table_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#conditional_insert_clause.
    def visitConditional_insert_clause(self, ctx:PlSqlParser.Conditional_insert_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#conditional_insert_when_part.
    def visitConditional_insert_when_part(self, ctx:PlSqlParser.Conditional_insert_when_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#conditional_insert_else_part.
    def visitConditional_insert_else_part(self, ctx:PlSqlParser.Conditional_insert_else_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#insert_into_clause.
    def visitInsert_into_clause(self, ctx:PlSqlParser.Insert_into_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#values_clause.
    def visitValues_clause(self, ctx:PlSqlParser.Values_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#merge_statement.
    def visitMerge_statement(self, ctx:PlSqlParser.Merge_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#merge_update_clause.
    def visitMerge_update_clause(self, ctx:PlSqlParser.Merge_update_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#merge_element.
    def visitMerge_element(self, ctx:PlSqlParser.Merge_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#merge_update_delete_part.
    def visitMerge_update_delete_part(self, ctx:PlSqlParser.Merge_update_delete_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#merge_insert_clause.
    def visitMerge_insert_clause(self, ctx:PlSqlParser.Merge_insert_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#selected_tableview.
    def visitSelected_tableview(self, ctx:PlSqlParser.Selected_tableviewContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lock_table_statement.
    def visitLock_table_statement(self, ctx:PlSqlParser.Lock_table_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#wait_nowait_part.
    def visitWait_nowait_part(self, ctx:PlSqlParser.Wait_nowait_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lock_table_element.
    def visitLock_table_element(self, ctx:PlSqlParser.Lock_table_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#lock_mode.
    def visitLock_mode(self, ctx:PlSqlParser.Lock_modeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#general_table_ref.
    def visitGeneral_table_ref(self, ctx:PlSqlParser.General_table_refContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#static_returning_clause.
    def visitStatic_returning_clause(self, ctx:PlSqlParser.Static_returning_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#error_logging_clause.
    def visitError_logging_clause(self, ctx:PlSqlParser.Error_logging_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#error_logging_into_part.
    def visitError_logging_into_part(self, ctx:PlSqlParser.Error_logging_into_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#error_logging_reject_part.
    def visitError_logging_reject_part(self, ctx:PlSqlParser.Error_logging_reject_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dml_table_expression_clause.
    def visitDml_table_expression_clause(self, ctx:PlSqlParser.Dml_table_expression_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_collection_expression.
    def visitTable_collection_expression(self, ctx:PlSqlParser.Table_collection_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#subquery_restriction_clause.
    def visitSubquery_restriction_clause(self, ctx:PlSqlParser.Subquery_restriction_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sample_clause.
    def visitSample_clause(self, ctx:PlSqlParser.Sample_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#seed_part.
    def visitSeed_part(self, ctx:PlSqlParser.Seed_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#condition.
    def visitCondition(self, ctx:PlSqlParser.ConditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#expressions_.
    def visitExpressions_(self, ctx:PlSqlParser.Expressions_Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#expression.
    def visitExpression(self, ctx:PlSqlParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cursor_expression.
    def visitCursor_expression(self, ctx:PlSqlParser.Cursor_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#logical_expression.
    def visitLogical_expression(self, ctx:PlSqlParser.Logical_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unary_logical_expression.
    def visitUnary_logical_expression(self, ctx:PlSqlParser.Unary_logical_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unary_logical_operation.
    def visitUnary_logical_operation(self, ctx:PlSqlParser.Unary_logical_operationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#logical_operation.
    def visitLogical_operation(self, ctx:PlSqlParser.Logical_operationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#multiset_expression.
    def visitMultiset_expression(self, ctx:PlSqlParser.Multiset_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#relational_expression.
    def visitRelational_expression(self, ctx:PlSqlParser.Relational_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#compound_expression.
    def visitCompound_expression(self, ctx:PlSqlParser.Compound_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#relational_operator.
    def visitRelational_operator(self, ctx:PlSqlParser.Relational_operatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#in_elements.
    def visitIn_elements(self, ctx:PlSqlParser.In_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#between_elements.
    def visitBetween_elements(self, ctx:PlSqlParser.Between_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#concatenation.
    def visitConcatenation(self, ctx:PlSqlParser.ConcatenationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#interval_expression.
    def visitInterval_expression(self, ctx:PlSqlParser.Interval_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_expression.
    def visitModel_expression(self, ctx:PlSqlParser.Model_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#model_expression_element.
    def visitModel_expression_element(self, ctx:PlSqlParser.Model_expression_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#single_column_for_loop.
    def visitSingle_column_for_loop(self, ctx:PlSqlParser.Single_column_for_loopContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#multi_column_for_loop.
    def visitMulti_column_for_loop(self, ctx:PlSqlParser.Multi_column_for_loopContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unary_expression.
    def visitUnary_expression(self, ctx:PlSqlParser.Unary_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#unary_expression_core.
    def visitUnary_expression_core(self, ctx:PlSqlParser.Unary_expression_coreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#implicit_cursor_expression.
    def visitImplicit_cursor_expression(self, ctx:PlSqlParser.Implicit_cursor_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#collection_expression.
    def visitCollection_expression(self, ctx:PlSqlParser.Collection_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#case_statement.
    def visitCase_statement(self, ctx:PlSqlParser.Case_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#simple_case_statement.
    def visitSimple_case_statement(self, ctx:PlSqlParser.Simple_case_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#searched_case_statement.
    def visitSearched_case_statement(self, ctx:PlSqlParser.Searched_case_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#case_when_part_statement.
    def visitCase_when_part_statement(self, ctx:PlSqlParser.Case_when_part_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#case_else_part_statement.
    def visitCase_else_part_statement(self, ctx:PlSqlParser.Case_else_part_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#case_expression.
    def visitCase_expression(self, ctx:PlSqlParser.Case_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#simple_case_expression.
    def visitSimple_case_expression(self, ctx:PlSqlParser.Simple_case_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#searched_case_expression.
    def visitSearched_case_expression(self, ctx:PlSqlParser.Searched_case_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#case_when_part_expression.
    def visitCase_when_part_expression(self, ctx:PlSqlParser.Case_when_part_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#case_else_part_expression.
    def visitCase_else_part_expression(self, ctx:PlSqlParser.Case_else_part_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#atom.
    def visitAtom(self, ctx:PlSqlParser.AtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#quantified_expression.
    def visitQuantified_expression(self, ctx:PlSqlParser.Quantified_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#string_function.
    def visitString_function(self, ctx:PlSqlParser.String_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#standard_function.
    def visitStandard_function(self, ctx:PlSqlParser.Standard_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_function.
    def visitJson_function(self, ctx:PlSqlParser.Json_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_object_content.
    def visitJson_object_content(self, ctx:PlSqlParser.Json_object_contentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_object_entry.
    def visitJson_object_entry(self, ctx:PlSqlParser.Json_object_entryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_table_clause.
    def visitJson_table_clause(self, ctx:PlSqlParser.Json_table_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_array_element.
    def visitJson_array_element(self, ctx:PlSqlParser.Json_array_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_on_null_clause.
    def visitJson_on_null_clause(self, ctx:PlSqlParser.Json_on_null_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_return_clause.
    def visitJson_return_clause(self, ctx:PlSqlParser.Json_return_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_transform_op.
    def visitJson_transform_op(self, ctx:PlSqlParser.Json_transform_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_column_clause.
    def visitJson_column_clause(self, ctx:PlSqlParser.Json_column_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_column_definition.
    def visitJson_column_definition(self, ctx:PlSqlParser.Json_column_definitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_query_returning_clause.
    def visitJson_query_returning_clause(self, ctx:PlSqlParser.Json_query_returning_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_query_return_type.
    def visitJson_query_return_type(self, ctx:PlSqlParser.Json_query_return_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_query_wrapper_clause.
    def visitJson_query_wrapper_clause(self, ctx:PlSqlParser.Json_query_wrapper_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_query_on_error_clause.
    def visitJson_query_on_error_clause(self, ctx:PlSqlParser.Json_query_on_error_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_query_on_empty_clause.
    def visitJson_query_on_empty_clause(self, ctx:PlSqlParser.Json_query_on_empty_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_value_return_clause.
    def visitJson_value_return_clause(self, ctx:PlSqlParser.Json_value_return_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_value_return_type.
    def visitJson_value_return_type(self, ctx:PlSqlParser.Json_value_return_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#json_value_on_mismatch_clause.
    def visitJson_value_on_mismatch_clause(self, ctx:PlSqlParser.Json_value_on_mismatch_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#literal.
    def visitLiteral(self, ctx:PlSqlParser.LiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#numeric_function_wrapper.
    def visitNumeric_function_wrapper(self, ctx:PlSqlParser.Numeric_function_wrapperContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#numeric_function.
    def visitNumeric_function(self, ctx:PlSqlParser.Numeric_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#listagg_overflow_clause.
    def visitListagg_overflow_clause(self, ctx:PlSqlParser.Listagg_overflow_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#other_function.
    def visitOther_function(self, ctx:PlSqlParser.Other_functionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#over_clause_keyword.
    def visitOver_clause_keyword(self, ctx:PlSqlParser.Over_clause_keywordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#within_or_over_clause_keyword.
    def visitWithin_or_over_clause_keyword(self, ctx:PlSqlParser.Within_or_over_clause_keywordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#standard_prediction_function_keyword.
    def visitStandard_prediction_function_keyword(self, ctx:PlSqlParser.Standard_prediction_function_keywordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#over_clause.
    def visitOver_clause(self, ctx:PlSqlParser.Over_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#windowing_clause.
    def visitWindowing_clause(self, ctx:PlSqlParser.Windowing_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#windowing_type.
    def visitWindowing_type(self, ctx:PlSqlParser.Windowing_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#windowing_elements.
    def visitWindowing_elements(self, ctx:PlSqlParser.Windowing_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#using_clause.
    def visitUsing_clause(self, ctx:PlSqlParser.Using_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#using_element.
    def visitUsing_element(self, ctx:PlSqlParser.Using_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#assignable_element.
    def visitAssignable_element(self, ctx:PlSqlParser.Assignable_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#collect_order_by_part.
    def visitCollect_order_by_part(self, ctx:PlSqlParser.Collect_order_by_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#within_or_over_part.
    def visitWithin_or_over_part(self, ctx:PlSqlParser.Within_or_over_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#string_delimiter.
    def visitString_delimiter(self, ctx:PlSqlParser.String_delimiterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cost_matrix_clause.
    def visitCost_matrix_clause(self, ctx:PlSqlParser.Cost_matrix_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_passing_clause.
    def visitXml_passing_clause(self, ctx:PlSqlParser.Xml_passing_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_attributes_clause.
    def visitXml_attributes_clause(self, ctx:PlSqlParser.Xml_attributes_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_namespaces_clause.
    def visitXml_namespaces_clause(self, ctx:PlSqlParser.Xml_namespaces_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_table_column.
    def visitXml_table_column(self, ctx:PlSqlParser.Xml_table_columnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_general_default_part.
    def visitXml_general_default_part(self, ctx:PlSqlParser.Xml_general_default_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_multiuse_expression_element.
    def visitXml_multiuse_expression_element(self, ctx:PlSqlParser.Xml_multiuse_expression_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmlroot_param_version_part.
    def visitXmlroot_param_version_part(self, ctx:PlSqlParser.Xmlroot_param_version_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmlroot_param_standalone_part.
    def visitXmlroot_param_standalone_part(self, ctx:PlSqlParser.Xmlroot_param_standalone_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmlserialize_param_enconding_part.
    def visitXmlserialize_param_enconding_part(self, ctx:PlSqlParser.Xmlserialize_param_enconding_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmlserialize_param_version_part.
    def visitXmlserialize_param_version_part(self, ctx:PlSqlParser.Xmlserialize_param_version_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmlserialize_param_ident_part.
    def visitXmlserialize_param_ident_part(self, ctx:PlSqlParser.Xmlserialize_param_ident_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#annotations_clause.
    def visitAnnotations_clause(self, ctx:PlSqlParser.Annotations_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#annotations_list.
    def visitAnnotations_list(self, ctx:PlSqlParser.Annotations_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#annotation.
    def visitAnnotation(self, ctx:PlSqlParser.AnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sql_plus_command.
    def visitSql_plus_command(self, ctx:PlSqlParser.Sql_plus_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#start_command.
    def visitStart_command(self, ctx:PlSqlParser.Start_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sql_plus_filepath.
    def visitSql_plus_filepath(self, ctx:PlSqlParser.Sql_plus_filepathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#whenever_command.
    def visitWhenever_command(self, ctx:PlSqlParser.Whenever_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#set_command.
    def visitSet_command(self, ctx:PlSqlParser.Set_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#timing_command.
    def visitTiming_command(self, ctx:PlSqlParser.Timing_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#clear_command.
    def visitClear_command(self, ctx:PlSqlParser.Clear_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#partition_extension_clause.
    def visitPartition_extension_clause(self, ctx:PlSqlParser.Partition_extension_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_alias.
    def visitColumn_alias(self, ctx:PlSqlParser.Column_aliasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_alias.
    def visitTable_alias(self, ctx:PlSqlParser.Table_aliasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#where_clause.
    def visitWhere_clause(self, ctx:PlSqlParser.Where_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#into_clause.
    def visitInto_clause(self, ctx:PlSqlParser.Into_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xml_column_name.
    def visitXml_column_name(self, ctx:PlSqlParser.Xml_column_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cost_class_name.
    def visitCost_class_name(self, ctx:PlSqlParser.Cost_class_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#attribute_name.
    def visitAttribute_name(self, ctx:PlSqlParser.Attribute_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#savepoint_name.
    def visitSavepoint_name(self, ctx:PlSqlParser.Savepoint_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#rollback_segment_name.
    def visitRollback_segment_name(self, ctx:PlSqlParser.Rollback_segment_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#schema_name.
    def visitSchema_name(self, ctx:PlSqlParser.Schema_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#routine_name.
    def visitRoutine_name(self, ctx:PlSqlParser.Routine_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#package_name.
    def visitPackage_name(self, ctx:PlSqlParser.Package_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#implementation_type_name.
    def visitImplementation_type_name(self, ctx:PlSqlParser.Implementation_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#parameter_name.
    def visitParameter_name(self, ctx:PlSqlParser.Parameter_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#reference_model_name.
    def visitReference_model_name(self, ctx:PlSqlParser.Reference_model_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#main_model_name.
    def visitMain_model_name(self, ctx:PlSqlParser.Main_model_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#container_tableview_name.
    def visitContainer_tableview_name(self, ctx:PlSqlParser.Container_tableview_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#aggregate_function_name.
    def visitAggregate_function_name(self, ctx:PlSqlParser.Aggregate_function_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#query_name.
    def visitQuery_name(self, ctx:PlSqlParser.Query_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#grantee_name.
    def visitGrantee_name(self, ctx:PlSqlParser.Grantee_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#role_name.
    def visitRole_name(self, ctx:PlSqlParser.Role_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#constraint_name.
    def visitConstraint_name(self, ctx:PlSqlParser.Constraint_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#label_name.
    def visitLabel_name(self, ctx:PlSqlParser.Label_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_name.
    def visitType_name(self, ctx:PlSqlParser.Type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#sequence_name.
    def visitSequence_name(self, ctx:PlSqlParser.Sequence_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#exception_name.
    def visitException_name(self, ctx:PlSqlParser.Exception_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#function_name.
    def visitFunction_name(self, ctx:PlSqlParser.Function_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#procedure_name.
    def visitProcedure_name(self, ctx:PlSqlParser.Procedure_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#trigger_name.
    def visitTrigger_name(self, ctx:PlSqlParser.Trigger_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#variable_name.
    def visitVariable_name(self, ctx:PlSqlParser.Variable_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#index_name.
    def visitIndex_name(self, ctx:PlSqlParser.Index_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#cursor_name.
    def visitCursor_name(self, ctx:PlSqlParser.Cursor_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#record_name.
    def visitRecord_name(self, ctx:PlSqlParser.Record_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#link_name.
    def visitLink_name(self, ctx:PlSqlParser.Link_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#local_link_name.
    def visitLocal_link_name(self, ctx:PlSqlParser.Local_link_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#connection_qualifier.
    def visitConnection_qualifier(self, ctx:PlSqlParser.Connection_qualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_name.
    def visitColumn_name(self, ctx:PlSqlParser.Column_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#tableview_name.
    def visitTableview_name(self, ctx:PlSqlParser.Tableview_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#xmltable.
    def visitXmltable(self, ctx:PlSqlParser.XmltableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#char_set_name.
    def visitChar_set_name(self, ctx:PlSqlParser.Char_set_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#synonym_name.
    def visitSynonym_name(self, ctx:PlSqlParser.Synonym_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#schema_object_name.
    def visitSchema_object_name(self, ctx:PlSqlParser.Schema_object_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#dir_object_name.
    def visitDir_object_name(self, ctx:PlSqlParser.Dir_object_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#user_object_name.
    def visitUser_object_name(self, ctx:PlSqlParser.User_object_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#grant_object_name.
    def visitGrant_object_name(self, ctx:PlSqlParser.Grant_object_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#column_list.
    def visitColumn_list(self, ctx:PlSqlParser.Column_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#paren_column_list.
    def visitParen_column_list(self, ctx:PlSqlParser.Paren_column_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#keep_clause.
    def visitKeep_clause(self, ctx:PlSqlParser.Keep_clauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#function_argument.
    def visitFunction_argument(self, ctx:PlSqlParser.Function_argumentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#function_argument_analytic.
    def visitFunction_argument_analytic(self, ctx:PlSqlParser.Function_argument_analyticContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#function_argument_modeling.
    def visitFunction_argument_modeling(self, ctx:PlSqlParser.Function_argument_modelingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#respect_or_ignore_nulls.
    def visitRespect_or_ignore_nulls(self, ctx:PlSqlParser.Respect_or_ignore_nullsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#argument.
    def visitArgument(self, ctx:PlSqlParser.ArgumentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#type_spec.
    def visitType_spec(self, ctx:PlSqlParser.Type_specContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#datatype.
    def visitDatatype(self, ctx:PlSqlParser.DatatypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#precision_part.
    def visitPrecision_part(self, ctx:PlSqlParser.Precision_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#native_datatype_element.
    def visitNative_datatype_element(self, ctx:PlSqlParser.Native_datatype_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#bind_variable.
    def visitBind_variable(self, ctx:PlSqlParser.Bind_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#general_element.
    def visitGeneral_element(self, ctx:PlSqlParser.General_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#general_element_part.
    def visitGeneral_element_part(self, ctx:PlSqlParser.General_element_partContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#table_element.
    def visitTable_element(self, ctx:PlSqlParser.Table_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#object_privilege.
    def visitObject_privilege(self, ctx:PlSqlParser.Object_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#system_privilege.
    def visitSystem_privilege(self, ctx:PlSqlParser.System_privilegeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#constant.
    def visitConstant(self, ctx:PlSqlParser.ConstantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#numeric.
    def visitNumeric(self, ctx:PlSqlParser.NumericContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#numeric_negative.
    def visitNumeric_negative(self, ctx:PlSqlParser.Numeric_negativeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#quoted_string.
    def visitQuoted_string(self, ctx:PlSqlParser.Quoted_stringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#identifier.
    def visitIdentifier(self, ctx:PlSqlParser.IdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#id_expression.
    def visitId_expression(self, ctx:PlSqlParser.Id_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#inquiry_directive.
    def visitInquiry_directive(self, ctx:PlSqlParser.Inquiry_directiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#outer_join_sign.
    def visitOuter_join_sign(self, ctx:PlSqlParser.Outer_join_signContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#regular_id.
    def visitRegular_id(self, ctx:PlSqlParser.Regular_idContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#non_reserved_keywords_in_18c.
    def visitNon_reserved_keywords_in_18c(self, ctx:PlSqlParser.Non_reserved_keywords_in_18cContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#non_reserved_keywords_in_12c.
    def visitNon_reserved_keywords_in_12c(self, ctx:PlSqlParser.Non_reserved_keywords_in_12cContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PlSqlParser#non_reserved_keywords_pre12c.
    def visitNon_reserved_keywords_pre12c(self, ctx:PlSqlParser.Non_reserved_keywords_pre12cContext):
        return self.visitChildren(ctx)



del PlSqlParser
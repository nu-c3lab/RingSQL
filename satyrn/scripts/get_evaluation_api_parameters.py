import json, random

with open('report_generation_info.json', 'r') as f:
    report_generation_info = json.load(f)

configurations = {}

for domain, domain_dict in report_generation_info.items():
    configurations[domain] = []
    for entity, entity_dict in domain_dict['entities'].items():
        for id_value in entity_dict['entity_instance_identifier_values']:
            for metric_dict in entity_dict['metrics']:
                for direction in metric_dict['metric_sort_direction']:
                    for target_val in metric_dict['benchmark_target']:
                        for time_range in metric_dict["time_zero_one"]:
                            for metric_set_filter in entity_dict['metric_set_filters']:
                                configurations[domain].append({
                                    'entity_name': entity_dict['entity_name'],
                                    'entity_instance_identifier_attribute_name': entity_dict['entity_instance_identifier_attribute_name'],
                                    'entity_instance_identifier_value': id_value,
                                    'metric_entity_name': metric_dict['metric_entity_name'],
                                    'metric_attribute_name': metric_dict['metric_attribute_name'],
                                    'metric_aggregation': metric_dict['metric_aggregation'],
                                    'metric_preference_direction': metric_dict['metric_preference_direction'],
                                    'metric_sort_direction': direction,
                                    'benchmark_target': target_val,
                                    'time_attribute_name': metric_dict['time_attribute'],
                                    'time_zero': time_range[0] if time_range else None,
                                    'time_one': time_range[1] if time_range else None,
                                    'metric_set_filter': metric_set_filter
                                })

final_configurations = {}
for domain, domain_configurations in configurations.items():
    final_configurations[domain] = []
    print(f'Configurations in {domain}: {len(domain_configurations)}')
    if len(domain_configurations) > 5:
        final_configurations[domain].extend(random.sample(domain_configurations, 5))
    else:
        final_configurations[domain].extend(domain_configurations)


with open('generation_parameter_configurations.json', 'w') as f:
    json.dump(final_configurations, f, indent=4)
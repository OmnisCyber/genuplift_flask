# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import PyPDF2
import json
import os
import io
import sys
import re
from flask import current_app as app
from flask import Flask, jsonify
from flask import Flask, request, render_template
from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from flask import Flask, request, redirect, flash
from flask_mail import Mail, Message
from flask import Flask, render_template, request, session

app = Flask(__name__)

@blueprint.route('/about')
@login_required
def index():
    return render_template('home/about.html', segment='about')


@blueprint.route('/<template>')
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment
        print("Chad = get_segment")

    except:
        return None

def extract_risk_genes_from_SNPs(txt_path, risk_map_path, verbose=True):
    with open(risk_map_path) as f:
        risk_map = json.loads(f.read())

    with open(txt_path) as f:
        SNP_txt = f.read()

    risk_genes = {}

    for snp in  risk_map.keys():
        i = SNP_txt.find(snp+'\t')
        if i > 0:
            line = SNP_txt[i:i+26]
            line = line.split('\n')[0]
            rsid = line.split('\t')[0]
            allele1 = line.split('\t')[-2]
            allele2 = line.split('\t')[-1]
            gene = risk_map[snp]['gene']
            variant = risk_map[snp]['variant']
            risk_allele = risk_map[snp]['risk_allele']
            alleles = allele1+allele2

            if verbose:
                print('examining: ', rsid, gene, variant, alleles, risk_allele)

            homozygousrisk = False
            for r in risk_allele:
                if alleles == r+r:
                    homozygousrisk=True
            if homozygousrisk:
                risk_genes[gene] = {
                    'variant': variant,
                    'rsid': snp,
                    'alleles': alleles,
                    'result': '+/+',
                }
                if verbose:
                    print('MATCH -- adding risk SNP: ', rsid, gene, variant, alleles, risk_allele)

    return risk_genes
    print("Chad = extract_genes_from_risk_snp")


def extract_text_from_pdf(pdf_path, start_marker, end_marker, verbose=True):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        start_extracting = False
        end_extracting = False
        text = ''
        extracted_text = {}
        for page in reader.pages:
            text = page.extract_text()
            break

        text = text.split(end_marker)[0]
        text = text.split(start_marker)[1]
        text = text.split('\n')
        text = [t for t in text if t != '']
        for i in range(int(len(text)/4)):
            elems = text[i*4:i*4+4]
            print(elems)
            gen_var = elems[0].replace('-0',' 0')
            gene = gen_var.split(' ')[0].upper()
            variant = gen_var.split(' ')[1].upper()

            if elems[3] == '+/+':
                extracted_text[gene] = {
                    'variant': variant,
                    'rsid': elems[1],
                    'alleles': elems[2],
                    'result': elems[3],
                }

        if verbose:
            print(f'extract from pdf: {extracted_text}')
        
        print("Chad = extract_text_from_pdf")
        return extracted_text

def read_to_dict(json_path):
    gene_vitamin_dict = {}
    with open(json_path) as f:
        d = json.loads(f.read())
    print("Chad = read_to_dict")
    return d

def find_genes_in_text(genes_in_text, gene_vitamin_dict, verbose=True):
    if verbose:
        print(f'raw gene list extracted from report: {genes_in_text}')
    output = {}
    for gene in genes_in_text.keys():
        variant = genes_in_text[gene]['variant']
        if verbose:
            print(f'checking: {gene} {variant} in map')
        gene = gene.strip()
        if gene in gene_vitamin_dict.keys():
            output[gene] = {}
            output[gene]['blurb'] = gene_vitamin_dict[gene]['blurb']
            if variant in gene_vitamin_dict[gene]['Variations'].keys():
                output[gene]['variant'] = gene_vitamin_dict[gene]['Variations'][variant]
                if verbose:
                    print(f"{gene} {variant} detected")
            else:
                if verbose:
                    print(f"{gene} {variant} NOT detected")
        else:
            if verbose:
                print(f"{gene} NOT detected")
    for word in output:
        print(word)
    if verbose:
        print(f'final output: {output}')

    # Use app.root_path to save to the root directory of the Flask app
    json_path = os.path.join(app.root_path, 'report.json')
    with open(json_path, 'w+') as f:
        f.write(json.dumps(output))

    print("Chad = find_Genes_in_text")

def find_genes_in_text(genes_in_text, gene_vitamin_dict, verbose=True):
    if verbose:
        print(f'raw gene list extracted from report: {genes_in_text}')
    output = {}
    for gene in genes_in_text.keys():
        variant = genes_in_text[gene]['variant']
        if verbose:
            print(f'checking: {gene} {variant} in map')
        gene = gene.strip()
        if gene in gene_vitamin_dict.keys():
            output[gene] = {}
            output[gene]['blurb'] = gene_vitamin_dict[gene]['blurb']
            if variant in gene_vitamin_dict[gene]['Variations'].keys():
                output[gene]['variant'] = gene_vitamin_dict[gene]['Variations'][variant]
                if verbose:
                    print(f"{gene} {variant} detected")
            else:
                if verbose:
                    print(f"{gene} {variant} NOT detected")
        else:
            if verbose:
                print(f"{gene} NOT detected")
    for word in output:
        print(word)

    json_path = os.path.join(app.root_path, 'report.json')
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    with open(json_path, 'w+') as f:
        f.write(json.dumps(output, indent=4))
    
    if verbose:
        print("Report saved to:", json_path)


@blueprint.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        file.save(os.path.join('uploads', file.filename))

        # Setup StringIO stream to capture prints
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Processing logic
        start_marker = "Result"
        end_marker = "Legend"
        genes_in_text = extract_risk_genes_from_SNPs(os.path.join('uploads', file.filename), 'risk_SNPs.json', verbose=True)
        gene_vitamin_dict = read_to_dict('gene_variation_to_vitamin.json')
        find_genes_in_text(genes_in_text, gene_vitamin_dict, verbose=True)

        # Reset stdout and get captured output
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        # Parse the captured output to structured data
        results = parse_output(output)
        
        print("Chad = upload_file")

        # Render results in response.html
        return render_template('home/response.html', results=results)
    return render_template('home/upload.html')

def parse_output(output):
    # Initialize structures to hold parsed data
    results = {
        'error': '',
        'matched_snps': [],
        'raw_gene_list': {},
        'genes_detected': [],
        'blurb': [],
    }

    # Regular expressions for matching lines
    match_pattern = re.compile(r'MATCH -- adding risk SNP: (.+)')
    gene_list_pattern = re.compile(r'raw gene list extracted from report: (.+)')
    detected_pattern = re.compile(r'(.+) detected')

    raw_list_str = ""

    # Iterate over each line in the output
    for line in output.split('\n'):
        if match := match_pattern.search(line):
            results['matched_snps'].append(match.group(1))
        elif gene_list := gene_list_pattern.search(line):
            raw_list_str += gene_list.group(1)
        elif detected := detected_pattern.search(line):
            results['genes_detected'].append(detected.group(1))
        elif detected := detected_pattern.search(line):
            results['blurb'].append(detected.group(1))

    print(results)

    print("Chad = parse_output]")

    # Attempt to parse the JSON string
    try:
        if raw_list_str:
            results['raw_gene_list'] = json.loads(raw_list_str)
    except json.JSONDecodeError as e:
        results['error'] = f"Error decoding JSON: {e}"
        # Attempt a manual parsing as a fallback
        try:
            results['raw_gene_list'] = eval(raw_list_str)
        except Exception as eval_e:
            results['error'] += f" | Also failed manual parsing: {eval_e}"

    return results

@blueprint.route('/report-data')
def report_data():
    json_path = os.path.join(app.root_path, 'report.json')  # Correctly reference app's root path
    with open(json_path) as json_file:
        data = json.load(json_file)
    return jsonify(data)

mail = Mail(app)

@blueprint.route('/send_message', methods=['POST'])
def send_message():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    
    msg = Message("Message from Your Website", sender='genuplift@gmail.com', recipients=['your-recipient@example.com'])
    msg.body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
    mail.send(msg)
    
    flash('Message sent successfully!', 'success')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
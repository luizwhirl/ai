import pandas as pd
import numpy as np
import re
from sklearn.tree import DecisionTreeClassifier, plot_tree, _tree
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt

def extract_treeRules(tree_model, feature_names, class_names):
    tree_ = tree_model.tree_
    feature_name = [
        feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!"
        for i in tree_.feature
    ]
    paths = []

    def recurse(node, path):
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            # Caminho da esquerda (menor ou igual)
            path.append(f"{name} <= {threshold:.2f}")
            recurse(tree_.children_left[node], path)
            path.pop()
            # Caminho da direita (maior)
            path.append(f"{name} > {threshold:.2f}")
            recurse(tree_.children_right[node], path)
            path.pop()
        else:
            # Chegou em uma folha
            value = tree_.value[node]
            class_idx = np.argmax(value)
            class_name = class_names[class_idx]
            regras_condicao = " E ".join(path)
            paths.append(f"SE {regras_condicao} ENTÃO Classe: {class_name}")

    recurse(0, [])
    return paths

def format_rule(regra_bruta, classe_alvo):
    regra = str(regra_bruta).strip('[]')
    
    if not regra:
        return f"SE [Nenhuma das condições acima for atendida] ENTÃO Classe: Não {classe_alvo}"
        
    regra = regra.replace('^', ' E ')
    regra = regra.replace('=>', ' >= ')
    regra = regra.replace('=<', ' <= ')
    regra = regra.replace('"', '')
    
    regra = re.sub(r'=(?:")?(-?\d+\.?\d*)-(-?\d+\.?\d*)(?:")?', r' entre \1 e \2', regra)
    regra = regra.replace('=', ' = ')
    regra = regra.replace(' < = ', ' <= ').replace(' > = ', ' >= ')
    
    return f"SE {regra} ENTÃO Classe: {classe_alvo}"

df_diabetes = pd.read_csv("diabetes_prediction_dataset.csv")

le = LabelEncoder()
df_diabetes['gender'] = le.fit_transform(df_diabetes['gender'])
df_diabetes['smoking_history'] = le.fit_transform(df_diabetes['smoking_history'])

X_diab = df_diabetes.drop('diabetes', axis=1)
y_diab = df_diabetes['diabetes']

df_students = pd.read_csv("Predict students' dropout and academic success.csv", sep=';')
if len(df_students.columns) == 1:
    df_students = pd.read_csv("Predict students' dropout and academic success.csv", sep=',')

X_stud = df_students.drop('Target', axis=1)
y_stud = df_students['Target']

def planNexecution(X, y, dataset_name, class_names):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    cart_model = DecisionTreeClassifier(criterion='gini', max_depth=3, random_state=42)
    cart_model.fit(X_train, y_train)
    
    c45_model = DecisionTreeClassifier(criterion='entropy', max_depth=3, random_state=42)
    c45_model.fit(X_train, y_train)
    
    print(f"\n==================================================")
    print(f"[{dataset_name}] BASE DE CONHECIMENTO - REGRAS CART (GINI)")
    print(f"==================================================")
    regras_cart = extract_treeRules(cart_model, list(X.columns), class_names)
    for r in regras_cart: print(r)
    
    print(f"\n--------------------------------------------------")
    print(f"[{dataset_name}] BASE DE CONHECIMENTO - REGRAS C4.5 (ENTROPIA)")
    print(f"--------------------------------------------------")
    regras_c45 = extract_treeRules(c45_model, list(X.columns), class_names)
    for r in regras_c45: print(r)

    plt.figure(figsize=(16, 8))
    plot_tree(cart_model, feature_names=list(X.columns), class_names=class_names, filled=True)
    plt.savefig(f"Arvore_CART_{dataset_name}.png", bbox_inches='tight')
    plt.close()
    
    plt.figure(figsize=(16, 8))
    plot_tree(c45_model, feature_names=list(X.columns), class_names=class_names, filled=True)
    plt.savefig(f"Arvore_C45_{dataset_name}.png", bbox_inches='tight')
    plt.close()

planNexecution(X_diab, y_diab, "Diabetes", ['Sem Diabetes', 'Com Diabetes'])
planNexecution(X_stud, y_stud, "Students_Dropout", list(y_stud.unique()))

print("\n\n" + "="*50)
print("ALGORITMO DE INDUÇÃO DE REGRAS (RIPPER)")
print("="*50)

try:
    import wittgenstein as lw
    
    X_train_d, _, y_train_d, _ = train_test_split(X_diab, y_diab, test_size=0.3, random_state=42)
    ripper_diab = lw.RIPPER()
    ripper_diab.fit(X_train_d, y_train_d)
    
    print("\n[Diabetes] Base de Regras Geradas pelo RIPPER:")
    for regra in ripper_diab.ruleset_:
        print(format_rule(regra, "Com Diabetes"))
        
    print(format_rule("", "Com Diabetes"))

    df_students_ripper = df_students.copy()
    df_students_ripper['Target'] = df_students_ripper['Target'].apply(lambda x: 1 if x == 'Dropout' else 0)
    
    X_stud_rip = df_students_ripper.drop('Target', axis=1)
    y_stud_rip = df_students_ripper['Target']
    
    X_train_s, _, y_train_s, _ = train_test_split(X_stud_rip, y_stud_rip, test_size=0.3, random_state=42)
    ripper_stud = lw.RIPPER()
    ripper_stud.fit(X_train_s, y_train_s)
    
    print("\n[Students_Dropout] Base de Regras Geradas pelo RIPPER:")
    for regra in ripper_stud.ruleset_:
        print(format_rule(regra, "Dropout (Desistência)"))
        
    print(format_rule("", "Dropout (Desistência)"))
        
except ImportError:
    print("\nBiblioteca 'wittgenstein' não encontrada.")
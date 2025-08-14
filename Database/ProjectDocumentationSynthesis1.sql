CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE "Cable"
( 
	"ID_cable" varchar(36) NOT NULL DEFAULT uuid_generate_v4(),
	"ID_project_document" varchar(36) NULL ,
	"Cable_identification" varchar(50) NULL ,
	"Purpose_purpose" varchar(50) NULL ,
	"Trassa_beginning" varchar(50) NULL ,
	"Trassa_end" varchar(50) NULL ,
	"Pipe_passage_designation" varchar(50) NULL ,
	"Pipe_passage_diameter" varchar(50) NULL ,
	"Pipe_passage_length" integer NULL ,
	"Draw_box_passing_length" integer NULL ,
	"Cable_or_wire_brand" varchar(50) NULL ,
	"Cable_or_wire_projet_cross_section" varchar(20) NULL ,
	"Cable_or_wire_projet_length" integer NULL ,
	"Cable_or_wire_laying_brand" varchar(50) NULL ,
	"Cable_or_wire_laying_cross_setion" varchar(20) NULL ,
	"Cable_or_wire_laying_length" integer NULL ,
	CONSTRAINT "XPKКабель_в_журнале" PRIMARY KEY ("ID_cable")
)
;



CREATE INDEX "XIF1Кабель_в_журнале" ON "Cable"
( 
	"ID_project_document"
)
;



CREATE INDEX "XIF2Кабель_в_журнале" ON "Cable"
( 
	"Cable_identification"
)
;



CREATE TABLE "ConstructionProject"
( 
	"ID_construction_project" varchar(36) NOT NULL DEFAULT uuid_generate_v4(),
	"Project_identification" varchar(100) NULL ,
	CONSTRAINT "XPKПроект_строительства" PRIMARY KEY ("ID_construction_project")
)
;



CREATE TABLE "DocumentSection"
( 
	"ID_document_section" varchar(36) NOT NULL DEFAULT uuid_generate_v4(),
	"ID_parent_section" varchar(36) NULL ,
	"ID_project_document" varchar(36) NOT NULL ,
	"Section_identification" varchar(50) NULL ,
	"Name_section" varchar(1024) NULL ,
	CONSTRAINT "XPKРаздел_проектного_документа" PRIMARY KEY ("ID_document_section")
)
;



CREATE INDEX "XIF1Раздел_проектного_документа" ON "DocumentSection"
( 
	"ID_project_document" 
)
;



CREATE TABLE "Equipment"
( 
	"ID_equipment" varchar(36) NOT NULL DEFAULT uuid_generate_v4(),
	"ID_project_document" varchar(36) NULL ,
	"ID_document_section" varchar(36) NULL ,
	"Equipment_identification" varchar(50) NULL,
	"Name_equipment" varchar(1024) NULL ,
	"Type_equipment" varchar(1024) NULL ,
	"Code_product" varchar(50) NULL ,
	"Supplier" varchar(100) NULL ,
	"Units" varchar(10) NULL ,
	"Quantity" integer NULL ,
	"Unit_mass" integer NULL ,
	"Note" text NULL ,
	CONSTRAINT "XPKОборудование_в_спецификации" PRIMARY KEY ("ID_equipment")
)
;



CREATE INDEX "XIF1Оборудование_в_спецификации" ON "Equipment"
( 
	"ID_document_section" 
)
;



CREATE INDEX "XIF2Оборудование_в_спецификации" ON "Equipment"
( 
	"ID_project_document" 
)
;



CREATE INDEX "XIF3Оборудование_в_спецификации" ON "Equipment"
( 
	"Equipment_identification" 
)
;



CREATE TABLE "LinkInEquipment"
( 
	"ID_project_document" varchar(36) NOT NULL,
	"ID_equipment" varchar(36) NOT NULL ,
	"Name_link" varchar(1024) NULL ,
	"ID_document_section" varchar(36) NULL ,
	"Обознаение_раздела" varchar(50) NULL ,
	CONSTRAINT "XPKСсылка_на_проектный_документ_в_спецификации" PRIMARY KEY ("ID_project_document","ID_equipment")
)
;



CREATE INDEX "XIF1Ссылка_на_проектный_документ_в_спецификации" ON "LinkInEquipment"
( 
	"ID_project_document" 
)
;



CREATE INDEX "XIF2Ссылка_на_проектный_документ_в_спецификации" ON "LinkInEquipment"
( 
	"ID_equipment" 
)
;



CREATE INDEX "XIF3Ссылка_на_проектный_документ_в_спецификации" ON "LinkInEquipment"
( 
	"ID_document_section" 
)
;



CREATE TABLE "LinkInSpecifiedWork"
( 
	"ID_project_document" varchar(36) NOT NULL,
	"ID_work" varchar(36) NOT NULL ,
	"Name_link" varchar(1024) NULL ,
	CONSTRAINT "XPKСсылка_на_проектный_документ_в_ведомости" PRIMARY KEY ("ID_project_document" ,"ID_work" )
)
;



CREATE INDEX "XIF1Ссылка_на_проектный_документ_в_ведомости" ON "LinkInSpecifiedWork"
( 
	"ID_project_document" 
)
;



CREATE INDEX "XIF2Ссылка_на_проектный_документ_в_ведомости" ON "LinkInSpecifiedWork"
( 
	"ID_work" 
)
;



CREATE TABLE "ProjectDocument"
( 
	"ID_project_document" varchar(36) NOT NULL DEFAULT uuid_generate_v4(),
	"File_name" varchar(1024) NULL ,
	"Document_type" varchar(3) NULL ,
	"ID_project_volume" varchar(36) NULL ,
	"Document_identification" varchar(50) NULL ,
	CONSTRAINT "XPKПроектный_документ" PRIMARY KEY ("ID_project_document" )
)
;



CREATE INDEX "XIF1Проектный_документ" ON "ProjectDocument"
( 
	"ID_project_volume" 
)
;



CREATE INDEX "XIF2Проектный_документ" ON "ProjectDocument"
( 
	"File_name" 
)
;



CREATE TABLE "ProjectVolume"
( 
	"ID_project_volume" varchar(36) NOT NULL DEFAULT uuid_generate_v4(),
	"Name_project_volume" varchar(1024) NULL ,
	"ID_construction_project" varchar(36) NULL ,
	CONSTRAINT "XPKТом_проекта" PRIMARY KEY ("ID_project_volume" )
)
;



CREATE INDEX "XIF1Том_проекта" ON "ProjectVolume"
( 
	"ID_construction_project" 
)
;



CREATE INDEX "XIF2Том_проекта" ON "ProjectVolume"
( 
	"Name_project_volume" 
)
;



CREATE TABLE "SpecifiedWork"
( 
	"ID_work" varchar(36) NOT NULL DEFAULT uuid_generate_v4(),
	"ID_project_document" varchar(36) NULL ,
	"ID_document_section" varchar(36) NULL ,
	"Work_identification" varchar(50) NULL ,
	"Name_work" varchar(1024) NULL ,
	"Units" varchar(10) NULL ,
	"Quantity" integer NULL ,
	"Note" text NULL ,
	CONSTRAINT "XPKРабота_в_ведомости" PRIMARY KEY ("ID_work" )
)
;



CREATE INDEX "XI1Работа_в_ведомости" ON "SpecifiedWork"
( 
	"ID_document_section" 
)
;



CREATE INDEX "XIF2Работа_в_ведомости" ON "SpecifiedWork"
( 
	"ID_project_document" 
)
;


CREATE INDEX "XIF3Работа_в_ведомости" ON "SpecifiedWork"
( 
	"Work_identification"
)
;




CREATE INDEX "XIF4Работа_в_ведомости" ON "SpecifiedWork"
( 
	"Name_work" 
)

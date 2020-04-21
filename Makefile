rwildcard=$(foreach d,$(wildcard $(1:=/*)),$(call rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))

CC	:=	gcc
CXX	:=	g++

SOURCES				:=	source
INCLUDES			:=	include
NOFORMAT_INCLUDES	:=	core/include \
						core/memecrypto \
						core/swshcrypto

NOFORMAT_SOURCES	:=	core/source/i18n \
						core/source/personal \
						core/source/pkx \
						core/source/sav \
						core/source/utils \
						core/source/wcx \
						core/swshcrypto \
						core/memecrypto

CFILES		:=	$(patsubst ./%,%,$(foreach dir,$(SOURCES),$(call rwildcard,$(dir),*.c))) $(patsubst ./%,%,$(foreach dir,$(NOFORMAT_SOURCES),$(call rwildcard,$(dir),*.c)))
CPPFILES	:=	$(patsubst ./%,%,$(foreach dir,$(SOURCES),$(call rwildcard,$(dir),*.cpp))) $(patsubst ./%,%,$(foreach dir,$(NOFORMAT_SOURCES),$(call rwildcard,$(dir),*.cpp)))
EXEC_NAME	:=	gallerypack
BUILD		:=	build

CFLAGS		:=	-Og -g -ffunction-sections $(foreach dir, $(INCLUDES), -I$(CURDIR)/$(dir)) $(foreach dir, $(NOFORMAT_INCLUDES), -I$(CURDIR)/$(dir))
CXXFLAGS	:=	$(CFLAGS) -std=gnu++17

OFILES			:=	$(CFILES:.c=.c.o) $(CPPFILES:.cpp=.cpp.o)
BUILD_OFILES	:=	$(subst //,/,$(subst /../,/__PrEvDiR/,$(subst /,//, $(OFILES))))
BUILD_OFILES	:=	$(patsubst ../%,__PrEvDiR/%,$(BUILD_OFILES))
BUILD_OFILES	:=	$(addprefix $(BUILD)/, $(BUILD_OFILES))
DEPSFILES		:=	$(BUILD_OFILES:.o=.d)

LD		:=	$(if $(CPPFILES),$(CXX),$(CC))
LDFLAGS	:=	-g -static -Wl,--gc-sections -lstdc++fs -lbz2

ifeq ($(OS),Windows_NT)
WHICH = where
else
WHICH = which
endif

.PHONY: all clean

all: $(EXEC_NAME)

clean:
	@rm -rf $(BUILD)
	@rm -f $(EXEC_NAME)

$(EXEC_NAME): $(BUILD_OFILES)
	$(LD) $(BUILD_OFILES) $(LDFLAGS) -o $@

$(BUILD)/%.c.o:
	$(eval CURRENT_PREREQ:=$(patsubst $(BUILD)/%,%,$(subst __PrEvDiR,..,$(@:.c.o=.c))))
	$(if $(wildcard $(CURRENT_PREREQ)),,$(error Prerequisite of $@ ($(CURRENT_PREREQ)) does not exist))
	@mkdir -p $(dir $@)
	$(CC) -MMD -MP -MF $(@:.o=.d) $(CFLAGS) -c -o $@ $(CURRENT_PREREQ)
	$(eval undefine CURRENT_PREREQ)

$(BUILD)/%.cpp.o:
	$(eval CURRENT_PREREQ:=$(patsubst $(BUILD)/%,%,$(subst __PrEvDiR,..,$(@:.cpp.o=.cpp))))
	$(if $(wildcard $(CURRENT_PREREQ)),,$(error Prerequisite of $@ ($(CURRENT_PREREQ)) does not exist))
	@mkdir -p $(dir $@)
	$(CXX) -MMD -MP -MF $(@:.o=.d) $(CXXFLAGS) -c -o $@ $(CURRENT_PREREQ)
	$(eval undefine CURRENT_PREREQ)

include $(wildcard $(DEPSFILES))